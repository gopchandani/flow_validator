__author__ = 'Rakesh Kumar'


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
from model.network_graph import NetworkGraph

class Experiment():

    def __init__(self,
                 num_iterations,
                 total_number_of_hosts,
                 load_config,
                 save_config,
                 controller,
                 experiment_switches):

        self.num_iterations = num_iterations
        self.total_number_of_hosts = total_number_of_hosts
        self.load_config = load_config
        self.save_config = save_config
        self.controller = controller
        self.topo_description = topo_description
        self.experiment_switches = experiment_switches

        # Data dictionaries in this case is keyed by the total_number_of_hosts that are added
        self.data = {
            "initial_port_graph_construction_time": defaultdict(list),
            "initial_traffic_set_propagation_time": defaultdict(list)
        }

        # Get the dockers ready
        self.cm = ControllerMan(len(self.total_number_of_hosts), controller=controller)

        if not load_config and save_config:
            cm = ControllerMan(1, controller=controller)
            controller_port = cm.get_next()

    def setup_controller(self):
        pass

    def setup_network(self, total_number_of_hosts):

        controller_port = 6633

        if not self.load_config and self.save_config:
            cm = ControllerMan(1, controller=self.controller)
            controller_port = cm.get_next()

        mm = MininetMan(controller_port, *self.topo_description)

        # Get a flow validator instance
        ng = NetworkGraph(mininet_man=mm, controller=self.controller, experiment_switches=self.experiment_switches,
                          save_config=self.save_config, load_config=self.load_config)

        if not self.load_config and self.save_config:
            if self.controller == "odl":
                mm.setup_mininet_with_odl(ng)
            elif self.controller == "ryu":
                #mm.setup_mininet_with_ryu_router()
                #mm.setup_mininet_with_ryu_qos(ng)
                mm.setup_mininet_with_ryu(ng)

        # Refresh the network_graph
        ng.parse_switches()
        fv = FlowValidator(ng)

    def trigger(self):

        print "Starting experiment..."
        for total_number_of_hosts in self.total_number_of_hosts:

            self.setup_network(total_number_of_hosts)
            ng = NetworkGraph(mininet_man=self.mm)

            for i in xrange(self.num_iterations):

                fv = FlowValidator(ng)
                with Timer(verbose=True) as t:
                    fv.init_port_graph()
                self.data["initial_port_graph_construction_time"][total_number_of_hosts].append(t.msecs)

                fv.add_hosts()
                with Timer(verbose=True) as t:
                    fv.initialize_admitted_traffic()

                self.data["initial_traffic_set_propagation_time"][total_number_of_hosts].append(t.msecs)

                fv.validate_all_host_pair_basic_reachability()

            self.mm.cleanup_mininet()

        print "Done..."

    def dump_data(self):
        pprint(self.data)
        with open("data/number_of_hosts_data_" + time.strftime("%Y%m%d_%H%M%S")+".json", "w") as outfile:
            json.dump(self.data, outfile)

    def __del__(self):
        self.dump_data()

def main():

    num_iterations = 100
    total_number_of_hosts = [2, 4]
    load_config = False
    save_config = True
    controller = "ryu"
    experiment_switches = ["s1", "s2"]

    exp = Experiment(num_iterations,
                     total_number_of_hosts,
                     [2, 4], "ryu")#, 6])#, 8, 10, 12, 14, 16])#, 18, 20])
    exp.trigger()

if __name__ == "__main__":
    main()