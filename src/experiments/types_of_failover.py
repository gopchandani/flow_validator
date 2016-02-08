__author__ = 'Rakesh Kumar'

import sys
sys.path.append("./")

import matplotlib.pyplot as plt

from collections import defaultdict
from timer import Timer
from analysis.flow_validator import FlowValidator
from experiment import Experiment


class TypesOfFailover(Experiment):

    def __init__(self,
                 num_iterations,
                 load_config,
                 save_config,
                 controller,
                 total_number_of_switches,
                 total_number_of_ports_to_synthesize,
                 edges_to_break):

        super(TypesOfFailover, self).__init__("types_of_failover",
                                              num_iterations,
                                              load_config,
                                              save_config,
                                              controller,
                                              1)

        self.total_number_of_switches = total_number_of_switches
        self.total_number_of_ports_to_synthesize = total_number_of_ports_to_synthesize
        self.edges_to_break = edges_to_break

        self.edges_broken = {}
        self.data["edges_broken"] = self.edges_broken

        # self.data = {
        #     "validation_time": defaultdict(defaultdict),
        # }

    def trigger(self):

        print "Starting experiment..."

        for number_of_ports_to_synthesize in xrange(1, self.total_number_of_ports_to_synthesize + 1):
            ports_to_synthesize = xrange(5000, 5000 + number_of_ports_to_synthesize )
            print "ports_to_synthesize:", ports_to_synthesize

            for number_of_switches in self.total_number_of_switches:
                print "number_of_switches_in_ring:", number_of_switches

                # Pick the last two switch numbers in the ring line topo

                self.topo_description = ("ringline", number_of_switches, 1)

                ng = self.setup_network_graph(self.topo_description,
                                              mininet_setup_gap=1,
                                              dst_ports_to_synthesize=ports_to_synthesize,
                                              synthesis_setup_gap=len(ports_to_synthesize))

                for (node1, node2) in self.edges_to_break:
                    s1 = node1[1:]
                    s2 = node2[1:]
                    self.data["edges_broken"][s1 + "<->" + s2] = []

                for i in xrange(self.num_iterations):

                    print "iteration:", i + 1

                    fv = FlowValidator(ng)
                    fv.init_network_port_graph()
                    fv.add_hosts()
                    fv.initialize_admitted_traffic()
                    fv.validate_all_host_pair_reachability()

                    for (node1, node2) in self.edges_to_break:
                        with Timer(verbose=True) as t:
                            #print "Breaking Edge:", node1, "<->", node2
                            fv.port_graph.remove_node_graph_edge(node1, node2)
                            fv.port_graph.add_node_graph_edge(node1, node2, updating=True)

                        s1 = node1[1:]
                        s2 = node2[1:]
                        self.data["edges_broken"][s1 + "<->" + s2].append(t.msecs)

                        #fv.validate_all_host_pair_reachability(verbose=True)

                        #print "Restoring Edge:", node1, "<->", node2
                        #fv.port_graph.add_node_graph_edge(node1, node2, updating=True)
                        #fv.validate_all_host_pair_reachability(verbose=True)

                    #
                    # for (node1, node2) in self.edges_to_break:
                    #     print "Restoring Edge:", node1, "<->", node2
                    #     fv.port_graph.add_node_graph_edge(node1, node2, updating=True)
                    #     fv.validate_all_host_pair_reachability(verbose=True)

                    fv.de_init_network_port_graph()

    def plot_types_of_failover(self):
        fig = plt.figure(0)
        self.plot_bar_error_bars("edges_broken", "Edge Broken", "Computation Time (ms)")

def main():

    num_iterations = 5
    load_config = False
    save_config = True
    controller = "ryu"

    total_number_of_switches = [8]
    total_number_of_ports_to_synthesize = 1
    edges_to_break = [('s1', 's2'), ('s1', 's4'), ('s2', 's3'), ('s3', 's4'), ('s3', 's8')]

    exp = TypesOfFailover(num_iterations,
                          load_config,
                          save_config,
                          controller,
                          total_number_of_switches,
                          total_number_of_ports_to_synthesize,
                          edges_to_break)

    exp.trigger()
    exp.dump_data()

    # Edge [('s1', 's2'), ('s1', 's4')]
    #exp.load_data("data/types_of_failover_2_iterations_20151203_141825.json")


    # Edge [('s2', 's3'), ('s3', 's4')]
    #exp.load_data("data/types_of_failover_2_iterations_20151203_150125.json")

    exp.plot_types_of_failover()

if __name__ == "__main__":
    main()