__author__ = 'Rakesh Kumar'

import json
import time
import numpy as np
import scipy.stats as ss
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from pprint import pprint
from controller_man import ControllerMan
from mininet_man import MininetMan
from model.network_graph import NetworkGraph

from synthesis.intent_synthesis import IntentSynthesis
from synthesis.intent_synthesis_ldst import IntentSynthesisLDST
from synthesis.intent_synthesis_load_balance import IntentSynthesisLB

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

        if not self.load_config and self.save_config:
            self.cm = ControllerMan(self.num_controller_instances, controller=controller)

    def setup_network_graph(self,
                            topo_description,
                            qos=False,
                            mininet_setup_gap=None,
                            dst_ports_to_synthesize=None,
                            synthesis_setup_gap=None,
                            synthesis_scheme="IntentSynthesis"):

        if not self.load_config and self.save_config:
            self.controller_port = self.cm.get_next()

        self.mm = MininetMan(synthesis_scheme, self.controller_port, *topo_description)

        if not self.load_config and self.save_config:
            self.mm.start_mininet()

            if mininet_setup_gap:
                time.sleep(mininet_setup_gap)

        # Get a flow validator instance
        ng = NetworkGraph(mm=self.mm,
                          controller=self.controller,
                          save_config=self.save_config,
                          load_config=self.load_config)

        if not self.load_config and self.save_config:

            if self.controller == "odl":
                self.mm.setup_mininet_with_odl(ng)
            elif self.controller == "ryu":
                #self.mm.setup_mininet_with_ryu_router()

                if qos:
                    self.mm.setup_mininet_with_ryu_qos(ng)
                else:
                    #self.mm.setup_mininet_with_ryu(ng, dst_ports_to_synthesize)

                    if synthesis_scheme == "IntentSynthesis":
                        self.synthesis = IntentSynthesis(ng, master_switch=topo_description[0] == "linear",
                                                         primary_paths_save_directory=ng.config_path_prefix)

                        self.synthesis.synthesize_all_node_pairs(dst_ports_to_synthesize)

                    elif synthesis_scheme == "IntentSynthesisLDST":
                        self.synthesis = IntentSynthesisLDST(ng, master_switch=topo_description[0] == "linear")
                        self.synthesis.synthesize_all_node_pairs(dst_ports_to_synthesize)

                    elif synthesis_scheme == "IntentSynthesisLB":
                        self.synthesis = IntentSynthesisLB(ng, master_switch=topo_description[0] == "linear")
                        self.synthesis.synthesize_all_node_pairs(dst_ports_to_synthesize)


                    self.mm.net.pingAll()
                    #is_bi_connected = self.mm.is_bi_connected_manual_ping_test()

                    # is_bi_connected = self.mm.is_bi_connected_manual_ping_test([(self.mm.net.get('h61'),
                    #                                                             self.mm.net.get('h71'))],
                    #                                                            [('s1', 's4')])

                    #print "is_bi_connected:", is_bi_connected

                if synthesis_setup_gap:
                    time.sleep(synthesis_setup_gap)

        # Refresh the network_graph
        ng.parse_switches()

        return ng

    def dump_data(self):
        pprint(self.data)
        filename = "data/" + self.experiment_tag + ".json"
        print "Writing to file:", filename

        with open(filename, "w") as outfile:
            json.dump(self.data, outfile)

    def load_data(self, filename):

        print "Reading file:", filename

        with open(filename, "r") as infile:
            self.data = json.load(infile)

    def prepare_matplotlib_data(self, data_dict):

        x = sorted(data_dict.keys())

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

    def plot_line_error_bars(self, data_key, x_label, y_label, y_scale='log'):

        markers = ['o', 'v', '^', '*', 'd']
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

            l = plt.errorbar(x, mean, sem, color="black", marker=markers[marker_i], markersize=8.0,
                             label="Ports Synthesized: " + str(number_of_ports_to_synthesize))

            marker_i += 1

        low_xlim = x_min
        high_xlim = x_max
        #
        # plt.xlim((low_xlim, high_xlim))
        # plt.xticks(range(low_xlim, high_xlim), fontsize=16)
        #
        # low_ylim = (0.9 * y_min) / 1000
        # high_ylim = (1.1 * y_max) / 1000
        #
        # plt.ylim((low_ylim, high_ylim))
        # plt.yticks(range(int(high_ylim/10), int(high_ylim), int(high_ylim/10)), fontsize=16)

        low_xlim, high_xlim = plt.xlim()
        plt.xlim(xmax=(high_xlim) *1.05)

        if y_scale == "linear":
            low_ylim, high_ylim = plt.ylim()
            plt.ylim(ymax=(high_ylim) *1.2)

        plt.yscale(y_scale)
        plt.xlabel(x_label, fontsize=18)
        plt.ylabel(y_label, fontsize=18)

        ax = plt.axes()
        xa = ax.get_xaxis()
        xa.set_major_locator(MaxNLocator(integer=True))

        legend = plt.legend(loc='upper left', shadow=True, fontsize=12)

        plt.savefig("plots/" + self.experiment_tag + "_" + data_key + ".png")
        plt.show()

    def plot_bar_error_bars(self, data_key, x_label, y_label):

        x, edges_broken_mean, edges_broken_sem = self.prepare_matplotlib_data(self.data[data_key])
        ind = np.arange(len(x))
        width = 0.3

        plt.bar(ind + width, edges_broken_mean, yerr=edges_broken_sem, color="0.90", align='center',
                error_kw=dict(ecolor='gray', lw=2, capsize=5, capthick=2))

        plt.xticks(ind + width, tuple(x))
        plt.xlabel(x_label, fontsize=18)
        plt.ylabel(y_label, fontsize=18)
        plt.savefig("plots/" + self.experiment_tag + "_" + data_key + ".png")
        plt.show()