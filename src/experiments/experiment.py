import json
import time
import random
import math
import numpy as np
import scipy.stats as ss
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from pprint import pprint
from controller_man import ControllerMan
from mininet_man import MininetMan

from model.network_graph import NetworkGraph
from model.match import Match
from model.traffic import Traffic
from timer import Timer

from synthesis.intent_synthesis import IntentSynthesis
from synthesis.synthesize_failover_aborescene import SynthesizeFailoverAborescene

__author__ = 'Rakesh Kumar'


class Experiment(object):

    def __init__(self,
                 experiment_name,
                 num_iterations,
                 load_config,
                 save_config,
                 controller,
                 num_controller_instances):

        self.experiment_tag = experiment_name + "_" + str(num_iterations) + "_iterations_" +time.strftime("%Y%m%d_%H%M%S")

        self.num_iterations = num_iterations
        self.load_config = load_config
        self.save_config = save_config
        self.controller = controller
        self.num_controller_instances = num_controller_instances

        self.data = {}

        self.controller_port = 6633
        self.cm = None
        self.mm = None
        self.ng = None
        self.synthesis = None

        if not self.load_config and self.save_config:
            self.cm = ControllerMan(self.num_controller_instances, controller=controller)

    def setup_network_graph(self,
                            topo_description,
                            mininet_setup_gap=None,
                            dst_ports_to_synthesize=None,
                            synthesis_setup_gap=None,
                            synthesis_scheme=None):

        if not self.load_config and self.save_config:
            self.controller_port = self.cm.get_next()

        self.mm = MininetMan(synthesis_scheme, self.controller_port, *topo_description,
                             dst_ports_to_synthesize=dst_ports_to_synthesize)

        if not self.load_config and self.save_config:
            self.mm.start_mininet()

            if mininet_setup_gap:
                time.sleep(mininet_setup_gap)

        # Get a flow validator instance
        self.ng = NetworkGraph(mm=self.mm,
                               controller=self.controller,
                               load_config=self.load_config,
                               save_config=self.save_config)

        if not self.load_config and self.save_config:
            if self.controller == "odl":
                self.mm.setup_mininet_with_odl(self.ng)
            elif self.controller == "ryu":
                if synthesis_scheme == "IntentSynthesis":
                    self.synthesis = IntentSynthesis(self.ng, master_switch=topo_description[0] == "linear",
                                                     synthesized_paths_save_directory=self.ng.config_path_prefix)

                    self.synthesis.synthesize_all_node_pairs(dst_ports_to_synthesize)

                elif synthesis_scheme == "Synthesis_Failover_Aborescene":
                    self.synthesis = SynthesizeFailoverAborescene(self.ng)

                    flow_match = Match(is_wildcard=True)
                    flow_match["ethernet_type"] = 0x0800
                    self.synthesis.synthesize_all_switches(flow_match, 2)

                # self.mm.net.pingAll()

                is_bi_connected = self.mm.is_bi_connected_manual_ping_test_all_hosts()

                #
                # is_bi_connected = self.mm.is_bi_connected_manual_ping_test([(self.mm.net.get('h11'),
                #                                                             self.mm.net.get('h31'))])

                # is_bi_connected = self.mm.is_bi_connected_manual_ping_test([(self.mm.net.get('h31'),
                #                                                             self.mm.net.get('h41'))],
                #                                                            [('s1', 's2')])
                # print "is_bi_connected:", is_bi_connected

                if synthesis_setup_gap:
                    time.sleep(synthesis_setup_gap)

        # Refresh the network_graph
        self.ng.parse_switches()

        print "total_flow_rules:", self.ng.total_flow_rules

        return self.ng

    #TODO: Eliminate the need to have this function
    def compare_synthesis_paths(self, analyzed_path, synthesized_path, verbose):

        path_matches = True

        if len(analyzed_path) == len(synthesized_path):
            i = 0
            for path_node in analyzed_path:
                if path_node.node_id != synthesized_path[i]:
                    path_matches = False
                    break
                i += 1
        else:
            path_matches = False

        return path_matches

    def search_matching_analyzed_path(self, analyzed_host_pairs_paths, src_host, dst_host, synthesized_path, verbose):

        found_matching_path = False

        # Need to find at least one matching analyzed path
        for analyzed_path in analyzed_host_pairs_paths[src_host][dst_host]:
            found_matching_path = self.compare_synthesis_paths(analyzed_path, synthesized_path, verbose)

            if found_matching_path:
                break

        return found_matching_path

    def compare_primary_paths_with_synthesis(self, fv, analyzed_host_pairs_traffic_paths, verbose=False):

        synthesized_primary_paths = None

        if not self.load_config and self.save_config:
            synthesized_primary_paths = self.synthesis.synthesis_lib.synthesized_primary_paths
        else:
            with open(self.ng.config_path_prefix + "synthesized_primary_paths.json", "r") as in_file:
                synthesized_primary_paths = json.loads(in_file.read())

        all_paths_match = True

        for src_host in analyzed_host_pairs_traffic_paths:
            for dst_host in analyzed_host_pairs_traffic_paths[src_host]:

                synthesized_path = synthesized_primary_paths[src_host][dst_host]
                path_matches = self.search_matching_analyzed_path(analyzed_host_pairs_traffic_paths,
                                                                  src_host, dst_host,
                                                                  synthesized_path, verbose)
                if not path_matches:
                    print "No analyzed path matched for:", synthesized_path
                    all_paths_match = False

        return all_paths_match

    def compare_failover_paths_with_synthesis(self, fv, links_to_try, verbose=False):

        synthesized_primary_paths = None
        synthesized_failover_paths = None
        
        if not self.load_config and self.save_config:
            synthesized_primary_paths = self.synthesis.synthesis_lib.synthesized_primary_paths
            synthesized_failover_paths = self.synthesis.synthesis_lib.synthesized_failover_paths
        else:
            with open(self.ng.config_path_prefix + "synthesized_primary_paths.json", "r") as in_file:
                synthesized_primary_paths = json.loads(in_file.read())
            
            with open(self.ng.config_path_prefix + "synthesized_failover_paths.json", "r") as in_file:
                synthesized_failover_paths = json.loads(in_file.read())

        for link in links_to_try:

            # Ignore host links
            if link[0].startswith("h") or link[1].startswith("h"):
                continue

            print "Breaking link:", link
            fv.port_graph.remove_node_graph_link(link[0], link[1])
            
            all_paths_match = True

            analyzed_host_pairs_paths = fv.get_all_host_pairs_traffic_paths()

            for src_host in analyzed_host_pairs_paths:
                for dst_host in analyzed_host_pairs_paths[src_host]:
                    
                    # If an link has been failed, first check both permutation of link switches, if neither is found,
                    # then refer to primary path by assuming that the given link did not participate in the failover of
                    # the given host pair.
                    try:
                        synthesized_path = synthesized_failover_paths[src_host][dst_host][link[0]][link[1]]
                    except:
                        try:
                            synthesized_path = synthesized_failover_paths[src_host][dst_host][link[1]][link[0]]
                        except:
                            synthesized_path = synthesized_primary_paths[src_host][dst_host]                        

                    path_matches = self.search_matching_analyzed_path(analyzed_host_pairs_paths,
                                                                      src_host, dst_host,
                                                                      synthesized_path, verbose)
                    if not path_matches:
                        print "No analyzed path matched for:", synthesized_path, "with failed link:", link
                        all_paths_match = False
                        break

            print "Restoring link:", link
            fv.port_graph.add_node_graph_link(link[0], link[1], updating=True)

            if not all_paths_match:
                break

        return all_paths_match

    def perform_incremental_times_experiment(self, fv, link_fraction_to_sample):

        all_links = list(fv.network_graph.get_switch_link_data())
        num_links_to_sample = int(math.ceil(len(all_links) * link_fraction_to_sample))

        incremental_times = []

        for i in range(num_links_to_sample):

            sampled_ld = random.choice(all_links)

            print "Failing:", sampled_ld
            with Timer(verbose=True) as t:
                fv.port_graph.remove_node_graph_link(sampled_ld.forward_link[0], sampled_ld.forward_link[1])
            incremental_times.append(t.secs)
            print incremental_times

            print "Restoring:", sampled_ld
            with Timer(verbose=True) as t:
                fv.port_graph.add_node_graph_link(sampled_ld.forward_link[0], sampled_ld.forward_link[1], updating=True)
            incremental_times.append(t.secs)
            print incremental_times

        return np.mean(incremental_times)

    def perform_policy_validation_experiment(self, fv):
        src_zone = [fv.network_graph.get_node_object(h_id).get_switch_port()
                    for h_id in fv.network_graph.host_ids]

        dst_zone = [fv.network_graph.get_node_object(h_id).get_switch_port()
                    for h_id in fv.network_graph.host_ids]

        traffic = Traffic(init_wildcard=True)
        traffic.set_field("ethernet_type", 0x0800)
        k = 1
        l = 12
        el = [random.choice(list(fv.network_graph.get_switch_link_data()))]

        with Timer(verbose=True) as t:
            validation_result = fv.validate_zone_pair_connectivity_path_length_link_exclusivity(src_zone,
                                                                                                dst_zone,
                                                                                                traffic,
                                                                                                l, el, k)
        # Return overall validation time, and incremental times [3] in validation results
        return t.secs, validation_result

    def dump_data(self):
        print "Dumping data:"
        pprint(self.data)
        filename = "data/" + self.experiment_tag + ".json"
        print "Writing to file:", filename

        with open(filename, "w") as outfile:
            json.dump(self.data, outfile)

    def load_data(self, filename):

        print "Reading file:", filename

        with open(filename, "r") as infile:
            self.data = json.load(infile)

        pprint(self.data)

    def prepare_matplotlib_data(self, data_dict):

        x = sorted(data_dict.keys(), key=int)

        data_means = []
        data_sems = []

        for p in x:
            mean = np.mean(data_dict[p])
            sem = ss.sem(data_dict[p])
            data_means.append(mean)
            data_sems.append(sem)

        return x, data_means, data_sems

    def get_data_min_max(self, data_dict):

        data_min = None
        data_max = None

        for p in data_dict:
            p_min = min(data_dict[p])

            if data_min:
                if p_min < data_min:
                    data_min = p_min
            else:
                data_min = p_min

            p_max = max(data_dict[p])
            if data_max:
                if p_max > data_max:
                    data_max = p_max
            else:
                data_max = p_max

        return data_min, data_max

    def plot_line_error_bars(self, data_key, x_label, y_label, y_scale='log', line_label="Ports Synthesized: ",
                             xmax_factor=1.05, xmin_factor=1.0, y_max_factor = 1.2, legend_loc='upper left',
                             xticks=None, xtick_labels=None, line_label_suffixes=None):

        markers = ['o', 'v', '^', '*', 'd', 'h', '+', '.']
        marker_i = 0

        x_min = None
        x_max = None

        y_min = None
        y_max = None

        data_vals = self.data[data_key]

        for number_of_ports_to_synthesize in data_vals:

            per_num_host_data = self.data[data_key][number_of_ports_to_synthesize]
            per_num_host_data = d = {int(k):v for k,v in per_num_host_data.items()}

            d_min, d_max =  self.get_data_min_max(per_num_host_data)
            if y_min:
                if d_min < y_min:
                    y_min = d_min
            else:
                y_min = d_min

            if y_max:
                if d_max > y_max:
                    y_max = d_max
            else:
                y_max = d_max

            x, mean, sem = self.prepare_matplotlib_data(per_num_host_data)

            d_min, d_max = min(map(int, x)), max(map(int, x))

            if x_min:
                if d_min < x_min:
                    x_min = d_min
            else:
                x_min = d_min

            if x_max:
                if d_max > x_max:
                    x_max = d_max
            else:
                x_max = d_max

            if line_label_suffixes:
                l = plt.errorbar(x, mean, sem, color="black", marker=markers[marker_i], markersize=8.0,
                                 label=line_label + line_label_suffixes[marker_i])
            else:
                l = plt.errorbar(x, mean, sem, color="black", marker=markers[marker_i], markersize=8.0,
                                 label=line_label + str(number_of_ports_to_synthesize))

            marker_i += 1

        low_xlim, high_xlim = plt.xlim()
        plt.xlim(xmax=(high_xlim) * xmax_factor)
        plt.xlim(xmin=(low_xlim) * xmin_factor)

        if y_scale == "linear":
            low_ylim, high_ylim = plt.ylim()
            plt.ylim(ymax=(high_ylim) * y_max_factor)

        plt.yscale(y_scale)
        plt.xlabel(x_label, fontsize=18)
        plt.ylabel(y_label, fontsize=18)

        ax = plt.axes()
        xa = ax.get_xaxis()
        xa.set_major_locator(MaxNLocator(integer=True))

        if xticks:
            ax.set_xticks(xticks)

        if xtick_labels:
            ax.set_xticklabels(xtick_labels)

        legend = plt.legend(loc=legend_loc, shadow=True, fontsize=12)

        plt.savefig("plots/" + self.experiment_tag + "_" + data_key + ".png")
        plt.show()

    def plot_lines_with_error_bars(self,
                                   ax,
                                   data_key,
                                   x_label,
                                   y_label,
                                   subplot_title,
                                   y_scale,
                                   x_min_factor=1.0,
                                   x_max_factor=1.05,
                                   y_min_factor=0.1,
                                   y_max_factor=1.5,
                                   xticks=None,
                                   xtick_labels=None,
                                   yticks=None,
                                   ytick_labels=None):

        ax.set_xlabel(x_label, fontsize=10, labelpad=-0)
        ax.set_ylabel(y_label, fontsize=10, labelpad=0)
        ax.set_title(subplot_title, fontsize=10)

        markers = ['.', 'v', 'o', 'd', '+', '^', 'H', ',', 's', 'o', 'h', '*']
        marker_i = 0

        for line_data_key in self.data[data_key]:

            data_vals = self.data[data_key][line_data_key]

            x, mean, sem = self.prepare_matplotlib_data(data_vals)

            ax.errorbar(x, mean, sem, color="black", marker=markers[marker_i], markersize=6.0, label=line_data_key, ls='none')

            marker_i += 1

        ax.tick_params(axis='x', labelsize=8)
        ax.tick_params(axis='y', labelsize=8)

        low_xlim, high_xlim = ax.get_xlim()
        ax.set_xlim(xmax=(high_xlim) * x_max_factor)
        ax.set_xlim(xmin=(low_xlim) * x_min_factor)

        if y_scale == "linear":
            low_ylim, high_ylim = ax.get_ylim()
            ax.set_ylim(ymin=low_ylim*y_min_factor)
            ax.set_ylim(ymax=high_ylim*y_max_factor)
        elif y_scale == "log":
            ax.set_ylim(ymin=10)
            ax.set_ylim(ymax=100000)

        ax.set_yscale(y_scale)

        xa = ax.get_xaxis()
        xa.set_major_locator(MaxNLocator(integer=True))

        if xticks:
            ax.set_xticks(xticks)

        if xtick_labels:
            ax.set_xticklabels(xtick_labels)

        if yticks:
            ax.set_yticks(yticks)

        if ytick_labels:
            ax.set_yticklabels(ytick_labels)
