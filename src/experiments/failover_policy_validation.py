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
            "initial_traffic_set_propagation_time": defaultdict(list),
            "failover_property_verification_time": defaultdict(list)
        }

        # Get the dockers ready
        self.cm = ControllerMan(len(topology_sizes))

    def setup_network(self, topology_size):

        # First get a docker for controller
        controller_port = self.cm.get_next()
        print "Controller Port", controller_port

        if self.topo == "ring":
            self.mm = MininetMan(controller_port, self.topo, topology_size, 1, ["s1", "s3"])
        elif self.topo == "fat_tree":
            dst_sw = "s" + str(topology_size)
            self.mm = MininetMan(controller_port, self.topo, topology_size, 1, ["s1", dst_sw])

        self.mm.setup_mininet_with_odl()

    def trigger(self):

        print "Starting experiment..."

        for topology_size in self.topology_sizes:

            self.setup_network(topology_size)
            
            num_switches = 0
            if self.topo == "fat_tree":
                num_switches = topology_size + 3
            else:
                num_switches = topology_size

            for i in range(self.num_iterations):

                fv = FlowValidator(self.mm.ng)
                fv.init_port_graph()
                fv.add_hosts()

                with Timer(verbose=True) as t:
                    fv.initialize_admitted_traffic()

                self.data["initial_traffic_set_propagation_time"][num_switches].append(t.msecs)

                # Just for debugging
                fv.validate_all_host_pair_basic_reachability()

                with Timer(verbose=True) as t:
                    fv.validate_all_host_pair_backup_reachability(self.mm.synthesis_dij.primary_path_edge_dict)

                self.data["failover_property_verification_time"][num_switches].append(t.msecs)

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


    exp = VaryingSizeTopology("ring", 100, [4, 6, 8, 10])#, 12, 14, 16, 18, 20])
#    exp = VaryingSizeTopology("ring", 100, [4])#, 6, 8, 10, 12, 14, 16, 18, 20])
#    exp = VaryingSizeTopology("fat_tree", 100, [3, 4, 5])#, 5, 6])
    exp.trigger()

if __name__ == "__main__":
    main()
