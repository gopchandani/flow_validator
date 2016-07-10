import matplotlib.pyplot as plt
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


class InitialIncrementalTimes(Experiment):
    def __init__(self,
                 num_iterations,
                 link_fraction_to_sample,
                 network_configurations):

        super(InitialIncrementalTimes, self).__init__("initial_incremental_policy_times",
                                                      num_iterations)

        self.network_configurations = network_configurations
        self.link_fraction_to_sample = link_fraction_to_sample

        self.data = {
            "initial_time": defaultdict(defaultdict),
            "incremental_time": defaultdict(defaultdict),
            "validation_time": defaultdict(defaultdict)
        }

    def trigger(self):

        print "Starting experiment..."

        for nc in self.network_configurations:
            print "network_configuration:", nc

            ng = nc.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

            self.data["initial_time"][nc.nc_topo_str][nc.topo_params["num_hosts_per_switch"]] = []
            self.data["incremental_time"][nc.nc_topo_str][nc.topo_params["num_hosts_per_switch"]] = []
            self.data["validation_time"][nc.nc_topo_str][nc.topo_params["num_hosts_per_switch"]] = []

            for i in xrange(self.num_iterations):
                print "iteration:", i + 1

                fv = FlowValidator(ng)
                with Timer(verbose=True) as t:
                    fv.init_network_port_graph()
                    fv.add_hosts()
                    fv.initialize_admitted_traffic()

                self.data["initial_time"][nc.nc_topo_str][nc.topo_params["num_hosts_per_switch"]].append(t.secs)
                self.dump_data()

                incr_time = self.perform_incremental_times_experiment(fv, self.link_fraction_to_sample)
                self.data["incremental_time"][nc.nc_topo_str][nc.topo_params["num_hosts_per_switch"]].append(incr_time)

                self.dump_data()

    def plot_initial_incremental_times(self):
        import pprint
        pprint.pprint(self.data)

        f, (ax1, ax2, ax3) = plt.subplots(1, 3, sharex=True, sharey=False, figsize=(9.5, 3.0))

        data_xtick_labels = list(self.data["all_keys"])
        data_xticks = [int(x) for x in data_xtick_labels]

        self.plot_lines_with_error_bars(ax1,
                                        "initial_time",
                                        "",
                                        "Time (seconds)",
                                        "(a)",
                                        y_scale='log',
                                        x_min_factor=1.0,
                                        x_max_factor=1.0,
                                        y_min_factor=0.01,
                                        y_max_factor=1,
                                        xticks=data_xticks,
                                        xtick_labels=data_xtick_labels)

        self.plot_lines_with_error_bars(ax2,
                                        "incremental_time",
                                        "Number of host pairs",
                                        "",
                                        "(b)",
                                        y_scale='log',
                                        x_min_factor=1.0,
                                        x_max_factor=1.0,
                                        y_min_factor=0.01,
                                        y_max_factor=1,
                                        xticks=data_xticks,
                                        xtick_labels=data_xtick_labels)

        self.plot_lines_with_error_bars(ax3,
                                        "relative_cost_ratio",
                                        "",
                                        "Relative Cost Ratio",
                                        "(c)",
                                        y_scale='linear',
                                        x_min_factor=1.0,
                                        x_max_factor=1.0,
                                        y_min_factor=0.1,
                                        y_max_factor=1.2,
                                        xticks=data_xticks,
                                        xtick_labels=data_xtick_labels,
                                        yticks=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

        # Shrink current axis's height by 25% on the bottom
        box = ax1.get_position()
        ax1.set_position([box.x0, box.y0 + box.height * 0.3,
                          box.width, box.height * 0.7])

        box = ax2.get_position()
        ax2.set_position([box.x0, box.y0 + box.height * 0.3,
                          box.width, box.height * 0.7])

        box = ax3.get_position()
        ax3.set_position([box.x0, box.y0 + box.height * 0.3,
                          box.width, box.height * 0.7])

        handles, labels = ax3.get_legend_handles_labels()

        ax1.legend(handles,
                   labels,
                   shadow=True,
                   fontsize=8,
                   loc='upper center',
                   ncol=3,
                   markerscale=1.0,
                   frameon=True,
                   fancybox=True,
                   columnspacing=0.5, bbox_to_anchor=[1.6, -0.25])

        plt.savefig("plots/" + self.experiment_tag + "_" + "initial_incremental_policy_times" + ".png", dpi=100)
        plt.show()

    def generate_relative_cost_ratio_data(self, data):

        data["relative_cost_ratio"] = defaultdict(defaultdict)
        for nc in data["initial_time"]:
            for nh in data["initial_time"][nc]:
                avg_initial_time = np.mean(data["initial_time"][nc][nh])
                avg_incremental_time = np.mean(data["incremental_time"][nc][nh])
                data["relative_cost_ratio"][nc][nh] = [avg_initial_time / avg_incremental_time]
        return data

    def generate_num_flow_path_keys(self, data):

        all_keys = set()

        flow_path_keys_data = {
            "initial_time": defaultdict(defaultdict),
            "incremental_time": defaultdict(defaultdict),
            "validation_time": defaultdict(defaultdict),
            "relative_cost_ratio": defaultdict(defaultdict)}

        for ds in data:
            for nc_topo_str in data[ds]:
                for nh in data[ds][nc_topo_str]:

                    num_host_carrying_switches = 0

                    if nc_topo_str == "Ring topology with 4 switches":
                        num_host_carrying_switches = 4
                    elif nc_topo_str == "Ring topology with 8 switches":
                        num_host_carrying_switches = 8
                    elif nc_topo_str == "Ring topology with 12 switches":
                        num_host_carrying_switches = 12
                    elif nc_topo_str == "Clos topology with 7 switches":
                        num_host_carrying_switches = 4
                    elif nc_topo_str == "Clos topology with 14 switches":
                        num_host_carrying_switches = 8
                    elif nc_topo_str == "Clos topology with 21 switches":
                        num_host_carrying_switches = 12
                    else:
                        raise Exception("Unknown topology, write the translation rule")

                    # Total flows = total hosts squared.
                    new_key = str(int(nh) * num_host_carrying_switches * int(nh) * num_host_carrying_switches)
                    flow_path_keys_data[ds][nc_topo_str][new_key] = data[ds][nc_topo_str][nh]

                    all_keys.add(new_key)

        flow_path_keys_data["all_keys"] = all_keys
        return flow_path_keys_data

    def load_data_merge_iterations(self, filename_list):

        '''
        :param filename_list: List of files with exact same network configurations in them
        :return: merged data
        '''

        merged_data = None

        for filename in filename_list:

            print "Reading file:", filename

            with open(filename, "r") as infile:
                this_data = json.load(infile)

            if merged_data:
                for ds in merged_data:
                    for nc in merged_data[ds]:
                        for nh in merged_data[ds][nc]:
                            try:
                                merged_data[ds][nc][nh].extend(this_data[ds][nc][nh])
                            except KeyError:
                                print nh, "not found."
            else:
                merged_data = this_data

        return merged_data

    def load_data_merge_network_config(self, data_dict_list):

        '''
        :param data_dict_list: List of dictionaries containing data from different network configurations
        :return: merged data
        '''

        merged_data = None

        for this_data in data_dict_list:

            if merged_data:
                for ds in merged_data:
                    merged_data[ds].update(this_data[ds])

            else:
                merged_data = this_data

        return merged_data

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

    def data_merge(self):

        path_prefix = "data_merge/initial_incremental_policy_times/"

        # # 4-switch ring merges
        # four_switch_ring_merge = self.load_data_merge_iterations([path_prefix + "4_switch_ring/iter1.json",
        #                                                           path_prefix + "4_switch_ring/iter2.json",
        #                                                           path_prefix + "4_switch_ring/iter3.json"])

        # 8-switch ring merges
        self.load_data_merge_nh([path_prefix + "8_switch_ring/iter1_hps/2_4_hps.json",
                                 path_prefix + "8_switch_ring/iter1_hps/6_hps.json"],
                                path_prefix + "8_switch_ring/iter1.json")

        self.load_data_merge_nh([path_prefix + "8_switch_ring/iter2_hps/2_4_hps.json",
                                 path_prefix + "8_switch_ring/iter2_hps/6_hps.json"],
                                path_prefix + "8_switch_ring/iter2.json")

        eight_switch_ring_merge = self.load_data_merge_iterations([path_prefix + "8_switch_ring/iter1.json",
                                                                   path_prefix + "8_switch_ring/iter2.json"])

        # 12-switch ring merges
        self.load_data_merge_nh([path_prefix + "12_switch_ring/iter1_hps/2_hps.json"],
                                path_prefix + "12_switch_ring/iter1.json")

        self.load_data_merge_nh([path_prefix + "12_switch_ring/iter2_hps/2_hps.json"],
                                path_prefix + "12_switch_ring/iter2.json")

        twelve_switch_ring_merge = self.load_data_merge_iterations([path_prefix + "12_switch_ring/iter1.json",
                                                                    path_prefix + "12_switch_ring/iter2.json"])


        # 7-switch clos merges
        seven_switch_clos_merge = self.load_data_merge_iterations([path_prefix + "7_switch_clos/iter1.json",
                                                                   path_prefix + "7_switch_clos/iter2.json"])

        # 14-switch clos merges
        self.load_data_merge_nh([path_prefix + "14_switch_clos/iter1_hps/2_hps.json",
                                 path_prefix + "14_switch_clos/iter1_hps/4_hps.json"],
                                path_prefix + "14_switch_clos/iter1.json")

        self.load_data_merge_nh([path_prefix + "14_switch_clos/iter2_hps/2_hps.json",
                                 path_prefix + "14_switch_clos/iter2_hps/4_hps.json"],
                                path_prefix + "14_switch_clos/iter2.json")

        self.load_data_merge_nh([path_prefix + "14_switch_clos/iter3_hps/4_hps.json"],
                                path_prefix + "14_switch_clos/iter3.json")

        fourteen_switch_clos_merge = self.load_data_merge_iterations([path_prefix + "14_switch_clos/iter1.json",
                                                                      path_prefix + "14_switch_clos/iter2.json",
                                                                      path_prefix + "14_switch_clos/iter3.json"])

        # 21-switch clos merges
        self.load_data_merge_nh([path_prefix + "21_switch_clos/iter1_hps/2_hps.json"],
                                path_prefix + "21_switch_clos/iter1.json")

        self.load_data_merge_nh([path_prefix + "21_switch_clos/iter2_hps/2_hps.json"],
                                path_prefix + "21_switch_clos/iter2.json")

        self.load_data_merge_nh([path_prefix + "21_switch_clos/iter3_hps/2_hps.json"],
                                path_prefix + "21_switch_clos/iter3.json")

        twenty_one_switch_clos_merge = self.load_data_merge_iterations([path_prefix + "21_switch_clos/iter1.json",
                                                                        path_prefix + "21_switch_clos/iter2.json",
                                                                        path_prefix + "21_switch_clos/iter3.json"])

        merged_data = self.load_data_merge_network_config([eight_switch_ring_merge,
                                                           twelve_switch_ring_merge,
                                                           seven_switch_clos_merge,
                                                           fourteen_switch_clos_merge,
                                                           twenty_one_switch_clos_merge])

        return merged_data


def get_network_configurations_list(num_hosts_per_switch_list):
    nc_list = []
    for hps in num_hosts_per_switch_list:
        # nc = NetworkConfiguration("ryu",
        #                           "clostopo",
        #                           {"fanout": 2,
        #                            "core": 2,
        #                            "num_hosts_per_switch": hps},
        #                           conf_root="configurations/",
        #                           synthesis_name="AboresceneSynthesis",
        #                           synthesis_params={"apply_group_intents_immediately": True})

        nc = NetworkConfiguration("ryu",
                                  "ring",
                                  {"num_switches": 4,
                                   "num_hosts_per_switch": hps},
                                  conf_root="configurations/",
                                  synthesis_name="AboresceneSynthesis",
                                  synthesis_params={"apply_group_intents_immediately": True})

        nc_list.append(nc)

    return nc_list


def main():

    num_iterations = 2
    link_fraction_to_sample = 0.25
    num_hosts_per_switch_list = [1, 2]#[2, 4]#, 6, 8, 10]
    network_configurations = get_network_configurations_list(num_hosts_per_switch_list)
    exp = InitialIncrementalTimes(num_iterations,
                                  link_fraction_to_sample,
                                  network_configurations)

    # Trigger the experiment
    exp.trigger()
    exp.dump_data()

    # exp.data = exp.data_merge()

    exp.data = exp.generate_relative_cost_ratio_data(exp.data)
    exp.data = exp.generate_num_flow_path_keys(exp.data)
    exp.plot_initial_incremental_times()

if __name__ == "__main__":
    main()
