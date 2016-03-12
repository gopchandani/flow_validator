__author__ = 'Rakesh Kumar'

import sys

sys.path.append("./")

import matplotlib.pyplot as plt
import numpy as np


from collections import defaultdict
from timer import Timer
from analysis.flow_validator import FlowValidator
from experiment import Experiment


class InitialIncrementalTimes(Experiment):
    def __init__(self,
                 num_iterations,
                 total_number_of_hosts,
                 load_config,
                 save_config,
                 controller,
                 fanout,
                 core,
                 total_number_of_ports_to_synthesize):

        super(InitialIncrementalTimes, self).__init__("initial_incremental_times",
                                                      num_iterations,
                                                      load_config,
                                                      save_config,
                                                      controller,
                                                      1)

        self.total_number_of_hosts = total_number_of_hosts
        self.total_number_of_ports_to_synthesize = total_number_of_ports_to_synthesize

        self.fanout = fanout
        self.core = core

        self.data = {
            "construction_time": defaultdict(defaultdict),
            "propagation_time": defaultdict(defaultdict),
            "incremental_avg_edge_failure_time": defaultdict(defaultdict),
            "incremental_avg_edge_restoration_time": defaultdict(defaultdict),
            "incremental_avg_edge_failure_restoration_time": defaultdict(defaultdict),
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

        for number_of_ports_to_synthesize in xrange(1, self.total_number_of_ports_to_synthesize + 1):
            ports_to_synthesize = xrange(5000, 5000 + number_of_ports_to_synthesize)
            print "ports_to_synthesize:", ports_to_synthesize

            for total_number_of_hosts in self.total_number_of_hosts:
                print "total_number_of_hosts:", total_number_of_hosts

                #self.topo_description = ("clostopo", None, total_number_of_hosts/4, self.fanout, self.core)
                self.topo_description = ("ring", 4, total_number_of_hosts/4, None, None)

                self.data["construction_time"][number_of_ports_to_synthesize][total_number_of_hosts] = []
                self.data["propagation_time"][number_of_ports_to_synthesize][total_number_of_hosts] = []
                self.data["incremental_avg_edge_failure_time"][number_of_ports_to_synthesize][total_number_of_hosts] = []
                self.data["incremental_avg_edge_restoration_time"][number_of_ports_to_synthesize][total_number_of_hosts] = []
                self.data["incremental_avg_edge_failure_restoration_time"][number_of_ports_to_synthesize][total_number_of_hosts] = []

                for i in xrange(self.num_iterations):
                    print "iteration:", i + 1

                    ng = self.setup_network_graph(self.topo_description,
                                                  mininet_setup_gap=1,
                                                  dst_ports_to_synthesize=ports_to_synthesize,
                                                  synthesis_setup_gap=len(ports_to_synthesize),
                                                  synthesis_scheme="IntentSynthesis")


                    self.fv = FlowValidator(ng)
                    with Timer(verbose=True) as t:
                        self.fv.init_network_port_graph()

                    self.data["construction_time"][number_of_ports_to_synthesize][total_number_of_hosts].append(t.msecs)

                    self.fv.add_hosts()

                    with Timer(verbose=True) as t:
                        self.fv.initialize_admitted_traffic()

                    self.data["propagation_time"][number_of_ports_to_synthesize][total_number_of_hosts].append(t.msecs)

                    fail, restore, fail_restore = self.perform_incremental_times()

                    self.data["incremental_avg_edge_failure_time"][number_of_ports_to_synthesize][total_number_of_hosts].append(fail)
                    self.data["incremental_avg_edge_restoration_time"][number_of_ports_to_synthesize][total_number_of_hosts].append(restore)
                    self.data["incremental_avg_edge_failure_restoration_time"][number_of_ports_to_synthesize][total_number_of_hosts].append(fail_restore)

                    del self.fv

                    #fv.de_init_network_port_graph()

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
    num_iterations = 5
    total_number_of_hosts = [4]
    load_config = False
    save_config = True
    controller = "ryu"

    fanout = 2
    core = 1
    total_number_of_ports_to_synthesize = 2

    exp = InitialIncrementalTimes(num_iterations,
                                  total_number_of_hosts,
                                  load_config,
                                  save_config,
                                  controller,
                                  fanout,
                                  core,
                                  total_number_of_ports_to_synthesize)

    exp.trigger()
    exp.dump_data()

    #exp.load_data("data/initial_incremental_times_5_iterations_20151206_141249.json")

    exp.plot_initial_incremental_times()


if __name__ == "__main__":
    main()
