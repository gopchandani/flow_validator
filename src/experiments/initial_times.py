import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

import sys
import json
import numpy as np

from collections import defaultdict
from timer import Timer
from analysis.flow_validator import FlowValidator
from experiment import Experiment
from network_configuration import NetworkConfiguration

__author__ = 'Rakesh Kumar'

sys.path.append("./")


class InitialTimes(Experiment):
    def __init__(self,
                 num_iterations,
                 network_configurations):

        super(InitialTimes, self).__init__("initial_times", num_iterations)

        self.network_configurations = network_configurations

        self.data = {
            "initial_time": defaultdict(defaultdict),
            "all_keys": []
        }

    def trigger(self):

        print "Starting experiment..."

        for nc in self.network_configurations:
            print "network_configuration:", nc

            nhps = None

            if nc.topo_name == "microgrid_topo":
                nhps = nc.topo_params["nHostsPerSwitch"]
            else:
                nhps = nc.topo_params["num_hosts_per_switch"]

            self.data["initial_time"][nc.nc_topo_str][nhps] = []

            for i in xrange(self.num_iterations):
                print "iteration:", i + 1

                fv = FlowValidator(nc.ng)
                with Timer(verbose=True) as t:
                    fv.init_network_port_graph()

                self.data["initial_time"][nc.nc_topo_str][nhps].append(t.secs)
                self.dump_data()

    def load_data_merge_nh(self, filename_list, merged_out_file):
        merged_data = None

        for filename in filename_list:
            print "Reading file:", filename
            with open(filename, "r") as infile:
                this_data = json.load(infile)
            if merged_data:
                for ds in merged_data:
                    for nc in merged_data[ds]:
                        merged_data[ds][nc].update(this_data[ds][nc])
            else:
                merged_data = this_data

        with open(merged_out_file, "w") as outfile:
            json.dump(merged_data, outfile)

        return merged_data

    def load_data_merge_network_config(self, data_dict_list):
        merged_data = None

        for this_data in data_dict_list:

            if merged_data:
                for ds in merged_data:
                    merged_data[ds].update(this_data[ds])

            else:
                merged_data = this_data

        return merged_data

    def generate_num_flow_path_keys(self, data):

        all_keys = set()

        flow_path_keys_data = {"initial_time": defaultdict(defaultdict)}

        for ds in data:
            for nc_topo_str in data[ds]:
                for nh in data[ds][nc_topo_str]:

                    num_host_carrying_switches = 0

                    if nc_topo_str == "Ring topology with 10 switches":
                        num_host_carrying_switches = 10
                    elif nc_topo_str == "Clos topology with 14 switches":
                        num_host_carrying_switches = 8
                    elif nc_topo_str == "Clique topology with 4 switches":
                        num_host_carrying_switches = 4
                    else:
                        print "nc_topo_str:", nc_topo_str
                        raise Exception("Unknown topology, write the translation rule")

                    # Total flows = total hosts squared.
                    new_key = str(int(nh) * num_host_carrying_switches * int(nh) * num_host_carrying_switches)
                    flow_path_keys_data[ds][nc_topo_str][new_key] = data[ds][nc_topo_str][nh]

                    all_keys.add(new_key)

        flow_path_keys_data["all_keys"] = list(all_keys)
        return flow_path_keys_data

    def merge_data(self):
        path_prefix = "data/14_switch_clos/"
        data_14_switch_clos = self.load_data_merge_nh([path_prefix + "2_4_hps.json",
                                                       path_prefix + "6_hps.json",
                                                       path_prefix + "8_hps.json",
                                                       path_prefix + "10_hps.json"],
                                                      path_prefix + "2_iter.json")

        path_prefix = "data/10_switch_ring/"
        data_10_switch_ring = self.load_data_merge_nh([path_prefix + "2_4_6_hps.json",
                                                       path_prefix + "8_hps.json",
                                                       path_prefix + "10_hps.json"],
                                                      path_prefix + "2_iter.json")

        path_prefix = "data/4_switch_clique/"
        data_4_switch_clique = self.load_data_merge_nh([path_prefix + "4_8_10_hps.json",
                                                        path_prefix + "20_hps.json",
                                                        path_prefix + "25_hps.json",
                                                        path_prefix + "16_hps.json"],
                                                      path_prefix + "2_iter.json")

        merged_data = self.load_data_merge_network_config([data_14_switch_clos,
                                                           data_10_switch_ring,
                                                           data_4_switch_clique])

        self.data = merged_data

        return self.data

    def merge_microgrid_data(self, microgrids_data_locations, current_data):
        current_data["initial_time"]["Microgrid Topology"] = defaultdict(list)
        ds = "initial_time"

        for loc in microgrids_data_locations:
            this_data = None
            with open(loc, "r") as infile:
                this_data = json.load(infile)
                nc_topo_str = this_data[ds].keys()[0]
                num_ug_switches = int(nc_topo_str.split()[3]) - 1
                num_sw_per_ug = 3
                num_microgrids = num_ug_switches / num_sw_per_ug
                nhps = int(nc_topo_str.split()[5])

                num_host_pairs = (num_microgrids * (nhps * num_sw_per_ug) * (nhps * num_sw_per_ug)) + ((num_microgrids + 1) * (num_microgrids + 1))

                current_data[ds]["Microgrid Topology"][str(num_host_pairs)] = this_data[ds][nc_topo_str][str(nhps)]
                current_data["all_keys"].append(str(num_host_pairs))

        return current_data

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
        ax.set_xlabel(x_label, fontsize=11, labelpad=-0)
        ax.set_ylabel(y_label, fontsize=11, labelpad=0)
        ax.set_title(subplot_title, fontsize=12)

        markers = ['.', 'x', '^', 'v', '*', '+', 'H', 's']
        marker_i = 0

        for line_data_key in sorted(self.data[data_key].keys()):

            style = None

            if line_data_key.find("0") == 3:
                style = "dotted"
            elif line_data_key.find("1") == 3:
                style = "dashed"
            elif line_data_key.find("2") == 3:
                style = "dashdot"
            elif line_data_key.find("3") == 3:
                style = "solid"

            data_vals = self.data[data_key][line_data_key]

            x, mean, sem = self.prepare_matplotlib_data(data_vals)

            ax.errorbar(x,
                        mean,
                        sem,
                        color="black",
                        marker=markers[marker_i],
                        markersize=7.0,
                        label=line_data_key)

            marker_i += 1

        ax.tick_params(axis='x', labelsize=11)
        ax.tick_params(axis='y', labelsize=11)

        low_xlim, high_xlim = ax.get_xlim()
        ax.set_xlim(xmax=(high_xlim) * x_max_factor)
        ax.set_xlim(xmin=(low_xlim) * x_min_factor)

        if y_scale == "linear":
            low_ylim, high_ylim = ax.get_ylim()
            ax.set_ylim(ymin=low_ylim * y_min_factor)
            ax.set_ylim(ymax=high_ylim * y_max_factor)
        elif y_scale == "log":
            ax.set_ylim(ymin=2)
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

    def plot_data(self, key, subkeys):
        f, (ax1) = plt.subplots(1, 1, sharex=True, sharey=False, figsize=(5.0, 4.0))

        data_xtick_labels = subkeys
        data_xticks = [int(x) for x in data_xtick_labels]

        self.plot_lines_with_error_bars(ax1,
                                        key,
                                        "Number of host pair traffic paths",
                                        "Time (seconds)",
                                        "",
                                        y_scale='log',
                                        x_min_factor=0.9,
                                        x_max_factor=1.10,
                                        y_min_factor=0.01,
                                        y_max_factor=10,
                                        xticks=data_xticks,
                                        xtick_labels=data_xtick_labels)

        xlabels = ax1.get_xticklabels()
        plt.setp(xlabels, rotation=45, fontsize=10)

        # Shrink current axis's height by 25% on the bottom
        box = ax1.get_position()
        ax1.set_position([box.x0, box.y0 + box.height * 0.3, box.width, box.height * 0.7])
        handles, labels = ax1.get_legend_handles_labels()

        ax1.legend(handles, labels, shadow=True, fontsize=10, loc='upper center', ncol=2, markerscale=1.0,
                   frameon=True, fancybox=True, columnspacing=3.5, bbox_to_anchor=[0.5, -0.25])

        plt.savefig("plots/" + self.experiment_tag + "_substation_mixed_policy_validation_times" + ".png", dpi=1000)
        plt.show()


def prepare_network_configurations(num_hosts_per_switch_list):
    nc_list = []
    for hps in num_hosts_per_switch_list:

        # nc = NetworkConfiguration("ryu",
        #                           "127.0.0.1",
        #                           6633,
        #                           "http://localhost:8080/",
        #                           "admin",
        #                           "admin",
        #                           "cliquetopo",
        #                           {"num_switches": 4,
        #                            "per_switch_links": 3,
        #                            "num_hosts_per_switch": hps},
        #                           conf_root="configurations/",
        #                           synthesis_name="AboresceneSynthesis",
        #                           synthesis_params={"apply_group_intents_immediately": True})

        # nc = NetworkConfiguration("ryu",
        #                           "127.0.0.1",
        #                           6633,
        #                           "http://localhost:8080/",
        #                           "admin",
        #                           "admin",
        #                           "ring",
        #                           {"num_switches": 10,
        #                            "num_hosts_per_switch": hps},
        #                           conf_root="configurations/",
        #                           synthesis_name="AboresceneSynthesis",
        #                           synthesis_params={"apply_group_intents_immediately": True})

        # nc = NetworkConfiguration("ryu",
        #                           "127.0.0.1",
        #                           6633,
        #                           "http://localhost:8080/",
        #                           "admin",
        #                           "admin",
        #                           "clostopo",
        #                           {"fanout": 2,
        #                            "core": 2,
        #                            "num_hosts_per_switch": hps},
        #                           conf_root="configurations/",
        #                           synthesis_name="AboresceneSynthesis",
        #                           synthesis_params={"apply_group_intents_immediately": True})

        ip_str = "172.17.0.2"
        port_str = "8181"
        num_grids = 3
        num_switches_per_grid = 3

        nc = NetworkConfiguration("onos",
                                  ip_str,
                                  int(port_str),
                                  "http://" + ip_str + ":" + port_str + "/onos/v1/",
                                  "karaf",
                                  "karaf",
                                  "microgrid_topo",
                                  {"num_switches": 1 + num_grids * num_switches_per_grid,
                                   "nGrids": num_grids,
                                   "nSwitchesPerGrid": num_switches_per_grid,
                                   "nHostsPerSwitch": hps},
                                  conf_root="configurations/",
                                  synthesis_name=None,
                                  synthesis_params=None)

        nc.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)
        nc_list.append(nc)

    return nc_list


def main():

    num_iterations = 2
    num_hosts_per_switch_list = [9]#[2, 4, 6, 8, 10]
    network_configurations = prepare_network_configurations(num_hosts_per_switch_list)
    exp = InitialTimes(num_iterations, network_configurations)

    # Trigger the experiment
    # exp.trigger()
    # exp.dump_data()

    exp.merge_data()
    exp.data = exp.generate_num_flow_path_keys(exp.data)
    exp.data = exp.merge_microgrid_data(microgrids_data_locations=[#"data/ugtopo/4_switch_3_hps.json",
                                                                   "data/ugtopo/4_switch_12_hps.json",
                                                                   #"data/ugtopo/7_switch_3_hps.json",
                                                                   "data/ugtopo/7_switch_12_hps.json",
                                                                   #"data/ugtopo/10_switch_3_hps.json",
                                                                   "data/ugtopo/10_switch_12_hps.json",
        #"data/ugtopo/10_switch_9_hps.json",
                                                                   #"data/ugtopo/16_switch_3_hps.json",
                                                                   "data/ugtopo/16_switch_12_hps.json",
                                                                   #"data/ugtopo/19_switch_3_hps.json",
                                                                   "data/ugtopo/19_switch_12_hps.json",
                                                                   #"data/ugtopo/13_switch_3_hps.json",
                                                                   "data/ugtopo/13_switch_12_hps.json"],
                                        current_data=exp.data)

    exp.dump_data()

    exp.data["all_keys"].remove('328')
    exp.data["all_keys"].remove('400')
    exp.data["all_keys"].remove('657')
    exp.data["all_keys"].remove('2304')
    exp.data["all_keys"].remove('6516')
    exp.data["all_keys"].remove('3904')

    exp.plot_data("initial_time", exp.data["all_keys"])

if __name__ == "__main__":
    main()