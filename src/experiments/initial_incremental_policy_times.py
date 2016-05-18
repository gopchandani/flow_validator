import matplotlib.pyplot as plt
import sys
import random
import json

from collections import defaultdict
from timer import Timer
from analysis.flow_validator import FlowValidator
from experiment import Experiment
from network_configuration import NetworkConfiguration
from model.traffic import Traffic

__author__ = 'Rakesh Kumar'

sys.path.append("./")


class InitialIncrementalTimes(Experiment):
    def __init__(self,
                 num_iterations,
                 link_fraction_to_sample,
                 num_hosts_per_switch_list,
                 network_configurations,
                 load_config,
                 save_config,
                 controller):

        super(InitialIncrementalTimes, self).__init__("initial_incremental_policy_times",
                                                      num_iterations,
                                                      load_config,
                                                      save_config,
                                                      controller,
                                                      1)

        self.num_hosts_per_switch_list = num_hosts_per_switch_list
        self.network_configurations = network_configurations
        self.link_fraction_to_sample = link_fraction_to_sample

        self.data = {
            "initial_time": defaultdict(defaultdict),
            "incremental_time": defaultdict(defaultdict),
            "validation_time": defaultdict(defaultdict)
        }

    def trigger(self):

        print "Starting experiment..."

        for network_configuration in self.network_configurations:
            print "network_configuration:", network_configuration

            for num_hosts_per_switch in self.num_hosts_per_switch_list:

                print "num_hosts_per_switch:", num_hosts_per_switch

                network_configuration.num_hosts_per_switch = num_hosts_per_switch

                topo_description = (network_configuration.topo_name,
                                    network_configuration.num_switches,
                                    num_hosts_per_switch,
                                    network_configuration.fanout,
                                    network_configuration.core)

                ng = self.setup_network_graph(topo_description,
                                              mininet_setup_gap=15,
                                              synthesis_setup_gap=15,
                                              synthesis_scheme="Synthesis_Failover_Aborescene")

                self.data["initial_time"][str(network_configuration)][num_hosts_per_switch] = []
                self.data["incremental_time"][str(network_configuration)][num_hosts_per_switch] = []
                self.data["validation_time"][str(network_configuration)][num_hosts_per_switch] = []

                for i in xrange(self.num_iterations):
                    print "iteration:", i + 1

                    fv = FlowValidator(ng)
                    with Timer(verbose=True) as t:
                        fv.init_network_port_graph()
                        fv.add_hosts()
                        fv.initialize_admitted_traffic()

                    self.data["initial_time"][str(network_configuration)][num_hosts_per_switch].append(t.secs)

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

                    self.data["validation_time"][str(network_configuration)][num_hosts_per_switch].append(t.secs)

                    print validation_result

                    self.data["incremental_time"][str(network_configuration)][num_hosts_per_switch].append(validation_result[3])

    def plot_initial_incremental_times(self):

        # Two subplots, unpack the axes array immediately
        f, (ax1, ax2, ax3) = plt.subplots(1, 3, sharex=True, sharey=True, figsize=(8.5, 2.5))

        self.plot_lines_with_error_bars(ax1,
                                        "initial_time",
                                        "",
                                        "Time (seconds)",
                                        "(a)",
                                        y_scale='log',
                                        x_min_factor=0.8,
                                        x_max_factor=1.2,
                                        y_min_factor=0.1,
                                        y_max_factor=10)

        self.plot_lines_with_error_bars(ax2,
                                        "incremental_time",
                                        "Total number of hosts",
                                        "",
                                        "(b)",
                                        y_scale='log',
                                        x_min_factor=0.8,
                                        x_max_factor=1.05,
                                        y_min_factor=0.1,
                                        y_max_factor=10)

        self.plot_lines_with_error_bars(ax3,
                                        "validation_time",
                                        "",
                                        "",
                                        "(c)",
                                        y_scale='log',
                                        x_min_factor=0.8,
                                        x_max_factor=1.05,
                                        y_min_factor=0.1,
                                        y_max_factor=10)

        plt.tight_layout(pad=0.1, w_pad=0.1, h_pad=0.1)

        handles, labels = ax3.get_legend_handles_labels()

        f.legend(handles,
                 labels,
                 shadow=False,
                 fontsize=10,
                 loc=8,
                 ncol=3,
                 markerscale=0.75,
                 frameon=True,
                 columnspacing=0.5, bbox_to_anchor=[0.5, 0.79])

        plt.savefig("plots/" + self.experiment_tag + "_" + "initial_incremental_policy_times" + ".png", dpi=100)
        plt.show()

    def load_data_merge_iterations(self, filename_list):

        '''
        :param filename_list: List of files with exact same experiment scenarios in them
        :return: merged dataset
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
                            merged_data[ds][nc][nh].extend(this_data[ds][nc][nh])
            else:
                merged_data = this_data

        return merged_data

def main():

    num_iterations = 1
    link_fraction_to_sample = 0.25
    num_hosts_per_switch_list = [2, 4, 6, 8, 10]

    # network_configurations = [NetworkConfiguration("ring", 4, 1, None, None),
    #                           NetworkConfiguration("clostopo", 7, 1, 2, 1)]

    # network_configurations = [NetworkConfiguration("clostopo", 7, 1, 2, 2)]
    network_configurations = [NetworkConfiguration("ring", 4, 1, None, None)]

    load_config = True
    save_config = False
    controller = "ryu"

    exp = InitialIncrementalTimes(num_iterations,
                                  link_fraction_to_sample,
                                  num_hosts_per_switch_list,
                                  network_configurations,
                                  load_config,
                                  save_config,
                                  controller)

    # exp.trigger()
    # exp.dump_data()

    exp.data = exp.load_data_merge_iterations(["data/initial_incremental_policy_times_1_iterations_20160517_174831.json",
                                               "data/initial_incremental_policy_times_1_iterations_20160517_174831.json"])

    # exp.load_data("data/initial_incremental_policy_times_1_iterations_20160517_174831.json")
    # exp.plot_initial_incremental_times()

if __name__ == "__main__":
    main()
