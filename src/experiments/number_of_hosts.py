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

class NumberOfHosts():

    def __init__(self, sample_size, total_number_of_hosts):

        self.num_iterations = sample_size
        self.total_number_of_hosts = total_number_of_hosts

        # Data dictionaries in this case is keyed by the total_number_of_hosts that are added
        self.data = {
            "initial_port_graph_construction_time": defaultdict(list),
            "initial_traffic_set_propagation_time": defaultdict(list)
        }

        # Get the dockers ready
        self.cm = ControllerMan(len(self.total_number_of_hosts))

    def setup_network(self, total_number_of_hosts):

        # First get a docker for controller
        controller_port = self.cm.get_next()
        print "Controller Port", controller_port

        self.mm = MininetMan(controller_port, "line", 2, total_number_of_hosts / 2, experiment_switches=["s1", "s2"])
        self.mm.setup_mininet()

    def trigger(self):

        print "Starting experiment..."
        for total_number_of_hosts in self.total_number_of_hosts:

            self.setup_network(total_number_of_hosts)

            for i in range(self.num_iterations):

                fv = FlowValidator(self.mm)
                with Timer(verbose=True) as t:
                    fv.init_port_graph()
                self.data["initial_port_graph_construction_time"][total_number_of_hosts].append(t.msecs)

                fv.add_hosts()

                with Timer(verbose=True) as t:
                    fv.initialize_admitted_traffic()

                self.data["initial_traffic_set_propagation_time"][total_number_of_hosts].append(t.msecs)

                #fv.validate_all_host_pair_basic_reachability()

            self.mm.cleanup_mininet()

        print "Done..."

    def dump_data(self):
        pprint(self.data)
        with open("data/number_of_hosts_data_" + time.strftime("%Y%m%d_%H%M%S")+".json", "w") as outfile:
            json.dump(self.data, outfile)

    def __del__(self):
        self.dump_data()

def main():

    exp = NumberOfHosts(100, [2, 4])#, 6, 8, 10, 12, 14, 16])#, 18, 20])
    exp.trigger()

if __name__ == "__main__":
    main()