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
        }

    def trigger(self):

        print "Starting experiment..."

        for nc in self.network_configurations:
            print "network_configuration:", nc

            self.data["initial_time"][nc.nc_topo_str][nc.topo_params["num_hosts_per_switch"]] = []

            for i in xrange(self.num_iterations):
                print "iteration:", i + 1

                fv = FlowValidator(nc.ng)
                with Timer(verbose=True) as t:
                    fv.init_network_port_graph()

                self.data["initial_time"][nc.nc_topo_str][nc.topo_params["num_hosts_per_switch"]].append(t.secs)
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

        merged_data = self.load_data_merge_network_config([data_14_switch_clos,
                                                           data_10_switch_ring])

        self.data = merged_data

        return self.data

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
                        label=line_data_key,
                        ls="none")

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
                                        "Number of host pairs",
                                        "Time (seconds)",
                                        "",
                                        y_scale='log',
                                        x_min_factor=1.0,
                                        x_max_factor=1,
                                        y_min_factor=0.01,
                                        y_max_factor=10,
                                        xticks=data_xticks,
                                        xtick_labels=data_xtick_labels)

        xlabels = ax1.get_xticklabels()
        plt.setp(xlabels, rotation=0, fontsize=10)

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
        #                           "ring",
        #                           {"num_switches": 10,
        #                            "num_hosts_per_switch": hps},
        #                           conf_root="configurations/",
        #                           synthesis_name="AboresceneSynthesis",
        #                           synthesis_params={"apply_group_intents_immediately": True})

        nc = NetworkConfiguration("ryu",
                                  "127.0.0.1",
                                  6633,
                                  "http://localhost:8080/",
                                  "admin",
                                  "admin",
                                  "clostopo",
                                  {"fanout": 2,
                                   "core": 2,
                                   "num_hosts_per_switch": hps},
                                  conf_root="configurations/",
                                  synthesis_name="AboresceneSynthesis",
                                  synthesis_params={"apply_group_intents_immediately": True})

        # nc = NetworkConfiguration("ryu",
        #                           "127.0.0.1",
        #                           6633,
        #                           "http://localhost:8080/",
        #                           "admin",
        #                           "admin",
        #                           "cliquetopo",
        #                           {"num_switches": 10,
        #                            "num_hosts_per_switch": hps,
        #                            "per_switch_links": 9},
        #                           conf_root="configurations/",
        #                           synthesis_name="AboresceneSynthesis",
        #                           synthesis_params={"apply_group_intents_immediately": True})

        nc.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

        nc_list.append(nc)

    return nc_list


def main():

    num_iterations = 1
    num_hosts_per_switch_list = [10]#[2, 4, 6]#[2, 4, 6, 8, 10]
    network_configurations = prepare_network_configurations(num_hosts_per_switch_list)
    exp = InitialTimes(num_iterations, network_configurations)
    # Trigger the experiment
    # exp.trigger()
    # exp.dump_data()

    exp.merge_data()
    exp.plot_data("initial_time", ["2", "4", "6", "8", "10"])


if __name__ == "__main__":
    main()
