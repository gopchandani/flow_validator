import matplotlib.pyplot as plt
import numpy as np
import sys

from collections import defaultdict
from timer import Timer
from analysis.flow_validator import FlowValidator
from experiment import Experiment

__author__ = 'Rakesh Kumar'
sys.path.append("./")

class InitialIncrementalTimes(Experiment):
    def __init__(self,
                 num_iterations,
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

        self.network_configurations = network_configurations

        self.data = {
            "construction_time": defaultdict(list),
            "propagation_time": defaultdict(list),
            "incremental_avg_edge_failure_time": defaultdict(list),
            "incremental_avg_edge_restoration_time": defaultdict(list),
            "incremental_avg_edge_failure_restoration_time": defaultdict(list),
        }

    def perform_incremental_times(self):
        fail_values = []
        restore_values = []
        fail_restore_values = []

        # Iterate over each edge
        for edge in self.fv.network_graph.graph.edges():

            # Ignore host edges
            if edge[0].startswith("h") or edge[1].startswith("h"):
                continue

            with Timer(verbose=True) as t:
                self.fv.port_graph.remove_node_graph_link(edge[0], edge[1])

            fail_time = t.msecs
            fail_values.append(fail_time)

            with Timer(verbose=True) as t:
                self.fv.port_graph.add_node_graph_link(edge[0], edge[1], updating=True)

            restore_time = t.msecs
            restore_values.append(restore_time)

            fail_restore_values.append(fail_time + restore_time)

        return np.mean(fail_values), np.mean(restore_values), np.mean(fail_restore_values)

    def trigger(self):

        print "Starting experiment..."

        for network_configuration in self.network_configurations:
            print "network_configuration:", network_configuration

            ng = self.setup_network_graph(network_configuration,
                                          mininet_setup_gap=15,
                                          synthesis_setup_gap=15,
                                          synthesis_scheme="Synthesis_Failover_Aborescene")

            for i in xrange(self.num_iterations):
                print "iteration:", i + 1

                self.fv = FlowValidator(ng)
                with Timer(verbose=True) as t:
                    self.fv.init_network_port_graph()

                self.data["construction_time"][str(network_configuration)].append(t.msecs)

                self.fv.add_hosts()

                with Timer(verbose=True) as t:
                    self.fv.initialize_admitted_traffic()

                self.data["propagation_time"][str(network_configuration)].append(t.msecs)
                #
                fail, restore, fail_restore = self.perform_incremental_times()

                self.data["incremental_avg_edge_failure_time"][str(network_configuration)].append(fail)
                self.data["incremental_avg_edge_restoration_time"][str(network_configuration)].append(restore)
                self.data["incremental_avg_edge_failure_restoration_time"][str(network_configuration)].append(fail_restore)

    def plot_initial_incremental_times(self):
        fig = plt.figure(0)
        self.plot_line_error_bars("construction_time",
                                  "Total number of hosts",
                                  "Average Construction Time (ms)")

        fig = plt.figure(1)
        self.plot_line_error_bars("propagation_time",
                                  "Total number of hosts",
                                  "Average Propagation Time (ms)")

        fig = plt.figure(2)
        self.plot_line_error_bars("incremental_avg_edge_failure_restoration_time",
                                  "Total number of hosts",
                                  "Average Incremental Computation Time (ms)",
                                  y_scale='linear')
def main():

    num_iterations = 1

#    network_configurations = [("ring", 4, 1, None, None)]#, ("clostopo", None, 1, 2, 1)]
#    network_configurations = [("clostopo", None, 5, 2, 1)]
    network_configurations = [("ring", 4, 1, None, None)]

    load_config = True
    save_config = False
    controller = "ryu"

    exp = InitialIncrementalTimes(num_iterations,
                                  network_configurations,
                                  load_config,
                                  save_config,
                                  controller)

    exp.trigger()
    exp.dump_data()

    #exp.load_data("data/.json")

    #exp.plot_initial_incremental_times()

if __name__ == "__main__":
    main()
