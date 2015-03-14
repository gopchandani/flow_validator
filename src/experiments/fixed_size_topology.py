__author__ = 'Rakesh Kumar'

import sys
import json
import time

sys.path.append("./")

from collections import defaultdict
from pprint import pprint

from timer import Timer
from analysis.flow_validator import FlowValidator
from controller_man import ControllerMan
from mininet_man import MininetMan

class FixedSizeTopology():

    def __init__(self, sample_size):

        self.num_iterations = sample_size

        # Data in this case is keyed by the primary path edges that we are going to break
        self.data = {}
        self.edges_broken = {}
        self.data["edges_broken"] = self.edges_broken

        # Get the dockers ready
        self.cm = ControllerMan(1)

    def setup_network(self, topology_size):

        # First get a docker for controller
        controller_port = self.cm.get_next()
        print "Controller Port", controller_port

        self.mm = MininetMan(controller_port, "ring", topology_size, 1, experiment_switches=["s1", "s6"])
        self.mm.setup_mininet()

    def trigger(self):

        print "Starting experiment..."

        self.setup_network(10)

        for (node1, node2) in self.mm.synthesis_dij.primary_path_edges:
            s1 = node1.split(":")[1]
            s2 = node2.split(":")[1]
            self.data["edges_broken"][s1 + "->" + s2] = []

        for i in range(self.num_iterations):

            fv = FlowValidator()
            fv.add_hosts()
            fv.initialize_admitted_match()

            for (node1, node2) in self.mm.synthesis_dij.primary_path_edges:

                with Timer(verbose=True) as t:
                    fv.model.simulate_remove_edge(node1, node2)
                    fv.port_graph.remove_node_graph_edge(node1, node2)
                    fv.model.simulate_add_edge(node1, node2)
                    fv.port_graph.add_node_graph_edge(node1, node2, True)

                s1 = node1.split(":")[1]
                s2 = node2.split(":")[1]
                self.data["edges_broken"][s1 + "->" + s2].append(t.msecs)

        print "Done..."
        self.dump_data()

    def dump_data(self):
        pprint(self.data)
        with open("data/fixed_size_topology_data_" + time.strftime("%Y%m%d_%H%M%S")+".json", "w") as outfile:
            json.dump(self.data, outfile)

    def __del__(self):
        self.dump_data()

def main():

    exp = FixedSizeTopology(100)
    exp.trigger()

if __name__ == "__main__":
    main()
