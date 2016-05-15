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
            "initial_time": defaultdict(list),
            "incremental_time": defaultdict(list),
        }

    def perform_incremental_times(self):
        incremental_times = []

        # Iterate over each edge
        for edge in self.fv.network_graph.graph.edges():

            # Ignore host edges
            if edge[0].startswith("h") or edge[1].startswith("h"):
                continue

            print "Failing:", edge

            with Timer(verbose=True) as t:
                self.fv.port_graph.remove_node_graph_link(edge[0], edge[1])
            incremental_times.append(t.msecs)

            print "Restoring:", edge

            with Timer(verbose=True) as t:
                self.fv.port_graph.add_node_graph_link(edge[0], edge[1], updating=True)
            incremental_times.append(t.msecs)

        return np.mean(incremental_times)

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
                    self.fv.add_hosts()
                    self.fv.initialize_admitted_traffic()

                self.data["initial_time"][str(network_configuration)].append(t.msecs)

                incremental_time = self.perform_incremental_times()

                self.data["incremental_time"][str(network_configuration)].append(incremental_time)


    def plot_initial_incremental_times(self):
        fig = plt.figure(0)
        self.plot_line_error_bars("initial_time",
                                  "Total number of hosts",
                                  "Average Initial Computation Time (ms)")

        fig = plt.figure(2)
        self.plot_line_error_bars("incremental_time",
                                  "Total number of hosts",
                                  "Average Incremental Computation Time (ms)",
                                  y_scale='linear')
def main():

    num_iterations = 1

#    network_configurations = [("ring", 4, 1, None, None)]#, ("clostopo", None, 1, 2, 1)]
#    network_configurations = [("clostopo", None, 1, 2, 1)]
    network_configurations = [("ring", 20, 1, None, None)]

    load_config = False
    save_config = True
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
