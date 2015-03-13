__author__ = 'Rakesh Kumar'

import sys
sys.path.append("./")

import json
import time

from collections import defaultdict
from pprint import pprint

from timer import Timer
from analysis.flow_validator import FlowValidator
from controller_man import ControllerMan
from mininet_man import MininetMan

class VaryingSizeTopology():

    def __init__(self, sample_size, topology_sizes):

        self.num_iterations = sample_size
        self.topology_sizes = topology_sizes

        self.data = {
            "init_times": defaultdict(list),
            "failover_update_times": defaultdict(list)
        }

        # Get the dockers ready
        self.cm = ControllerMan(len(topology_sizes))

    def setup_network(self, topology_size):

        # First get a docker for controller
        controller_port = self.cm.get_next()
        print "Controller Port", controller_port

        self.mm = MininetMan(controller_port, "ring", topology_size, 1)
        self.mm.setup_mininet()

    def trigger(self):

        print "Starting experiment..."

        for topology_size in self.topology_sizes:

            self.setup_network(topology_size)
            for i in range(self.num_iterations):

                fv = FlowValidator()
                fv.add_hosts()

                with Timer(verbose=True) as t:
                    fv.initialize_admitted_match()

                self.data["init_times"][topology_size].append(t.msecs)

                with Timer(verbose=True) as t:

                    # First remove the edge
                    node1 = "openflow:4"
                    node2 = "openflow:3"

                    fv.model.simulate_remove_edge(node1, node2)
                    fv.port_graph.remove_node_graph_edge(node1, node2)
                    fv.model.simulate_add_edge(node1, node2)
                    fv.port_graph.add_node_graph_edge(node1, node2, True)

                self.data["failover_update_times"][topology_size].append(t.msecs)

        print "Done..."
        self.dump_data()

    def dump_data(self):
        pprint(self.data)
        with open("data/data_" + time.strftime("%Y%m%d_%H%M%S")+".json", "w") as outfile:
            json.dump(self.data, outfile)

    def __del__(self):
        self.dump_data()

def main():

    exp = VaryingSizeTopology(50, [4, 6, 8, 10, 12, 14, 16, 18, 20])
    exp.trigger()

if __name__ == "__main__":
    main()
