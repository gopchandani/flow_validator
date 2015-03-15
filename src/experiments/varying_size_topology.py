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

    def __init__(self, topo, sample_size, topology_sizes):

        self.num_iterations = sample_size
        self.topology_sizes = topology_sizes
        self.topo = topo

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

        self.mm = MininetMan(controller_port, self.topo, topology_size, 1)
        self.mm.setup_mininet()

    # returns list of length of admitted matches
    def admitted_lengths(self, fv):

        admitted_lengths = []

        for src_h_id in fv.model.get_host_ids():
            for dst_h_id in fv.model.get_host_ids():

                src_host_obj = fv.model.get_node_object(src_h_id)
                dst_host_obj = fv.model.get_node_object(dst_h_id)

                if src_h_id != dst_h_id:
                    if dst_host_obj.ingress_port.port_id in src_host_obj.egress_port.admitted_traffic:
                        at = src_host_obj.egress_port.admitted_traffic[dst_host_obj.ingress_port.port_id]
                        admitted_lengths.append(len(at.match_elements))
                    else:
                        admitted_lengths.append(0)

        return admitted_lengths


    def trigger(self):

        print "Starting experiment..."

        for topology_size in self.topology_sizes:

            self.setup_network(topology_size)
            for i in range(self.num_iterations):

                fv = FlowValidator()
                fv.add_hosts()

                with Timer(verbose=True) as t:
                    fv.initialize_admitted_match()

                admitted_lengths = self.admitted_lengths(fv)
                print admitted_lengths

                self.data["init_times"][topology_size].append(t.msecs)

                # Take the first edge in the primary path and try to break it
                node1, node2 = self.mm.synthesis_dij.primary_path_edges[0]

                with Timer(verbose=True) as t:

                    fv.model.simulate_remove_edge(node1, node2)
                    fv.port_graph.remove_node_graph_edge(node1, node2)
                    fv.model.simulate_add_edge(node1, node2)
                    fv.port_graph.add_node_graph_edge(node1, node2, True)

                self.data["failover_update_times"][topology_size].append(t.msecs)

        print "Done..."
        self.dump_data()

    def dump_data(self):
        pprint(self.data)
        with open("data/variable_size_topology_" + self.topo + "_data_" + time.strftime("%Y%m%d_%H%M%S")+".json", "w") as outfile:
            json.dump(self.data, outfile)

    def __del__(self):
        self.dump_data()
        self.mm.cleanup_mininet()

def main():

    exp = VaryingSizeTopology("ring", 100, [4])#, 6, 8, 10, 12, 14, 16, 18, 20])
#    exp = VaryingSizeTopology("fat_tree", 100, [3])#, 4, 5, 6])
    exp.trigger()

if __name__ == "__main__":
    main()
