import matplotlib.pyplot as plt
import numpy as np
import sys

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
                 num_hosts_per_switch_list,
                 network_configurations,
                 load_config,
                 save_config,
                 controller):

        super(InitialIncrementalTimes, self).__init__("initial_incremental_times",
                                                      num_iterations,
                                                      load_config,
                                                      save_config,
                                                      controller,
                                                      1)

        self.num_hosts_per_switch_list = num_hosts_per_switch_list
        self.network_configurations = network_configurations

        self.data = {
            "initial_time": defaultdict(defaultdict),
            "incremental_time": defaultdict(defaultdict),
        }

    def perform_incremental_times(self, fv):
        incremental_times = []

        # Iterate over each edge
        for edge in fv.network_graph.graph.edges():

            # Ignore host edges
            if edge[0].startswith("h") or edge[1].startswith("h"):
                continue

            print "Failing:", edge

            with Timer(verbose=True) as t:
                fv.port_graph.remove_node_graph_link(edge[0], edge[1])
            incremental_times.append(t.msecs)

            print "Restoring:", edge

            with Timer(verbose=True) as t:
                fv.port_graph.add_node_graph_link(edge[0], edge[1], updating=True)
            incremental_times.append(t.msecs)

        return np.mean(incremental_times)

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
                self.data["incremental_time"][str(network_configuration)][num_hosts_per_switch]= []

                for i in xrange(self.num_iterations):
                    print "iteration:", i + 1

                    fv = FlowValidator(ng)
                    with Timer(verbose=True) as t:
                        fv.init_network_port_graph()
                        fv.add_hosts()
                        fv.initialize_admitted_traffic()

                    self.data["initial_time"][str(network_configuration)][num_hosts_per_switch].append(t.msecs)

                    incremental_time = self.perform_incremental_times(fv)

                    self.data["incremental_time"][str(network_configuration)][num_hosts_per_switch].append(incremental_time)

    def plot_initial_incremental_times(self):

        fig = plt.figure(0)
        self.plot_lines_with_error_bars("initial_time",
                                  "Total number of hosts",
                                  "Average Initial Computation Time (ms)",
                                  y_scale='linear',
                                  xmin_factor=0,
                                  xmax_factor=1.05,
                                  y_max_factor=1.05,
                                  legend_loc='upper right',
                                  xticks=self.num_hosts_per_switch_list)

        fig = plt.figure(1)
        self.plot_lines_with_error_bars("incremental_time",
                                  "Total number of hosts",
                                  "Average Incremental Computation Time (ms)",
                                  y_scale='linear',
                                  xmin_factor=0,
                                  xmax_factor=1.05,
                                  y_max_factor=1.05,
                                  legend_loc='upper right',
                                  xticks=self.num_hosts_per_switch_list)


def main():

    num_iterations = 2
    num_hosts_per_switch_list = [1, 2, 3, 4, 5, 6]

    network_configurations = [NetworkConfiguration("ring", 4, 1, None, None),
                              NetworkConfiguration("clostopo", 7, 1, 2, 1)]

    # network_configurations = [NetworkConfiguration("clostopo", 7, 1, 2, 1)]

    # network_configurations = [NetworkConfiguration("ring", 4, 1, None, None)]

    load_config = False
    save_config = True
    controller = "ryu"

    exp = InitialIncrementalTimes(num_iterations,
                                  num_hosts_per_switch_list,
                                  network_configurations,
                                  load_config,
                                  save_config,
                                  controller)

    # exp.trigger()
    # exp.dump_data()

    exp.load_data("data/initial_incremental_times_2_iterations_20160516_172555.json")
    exp.plot_initial_incremental_times()

if __name__ == "__main__":
    main()
