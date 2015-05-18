__author__ = 'Rakesh Kumar'

import sys
import json
import time
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as ss


sys.path.append("./")

from collections import defaultdict
from pprint import pprint

from timer import Timer
from analysis.flow_validator import FlowValidator
from controller_man import ControllerMan
from mininet_man import MininetMan
from model.network_graph import NetworkGraph

class NumberOfHosts():

    def __init__(self,
                 num_iterations,
                 total_number_of_hosts,
                 load_config,
                 save_config,
                 controller,
                 experiment_switches):

        self.experiment_tag = "number_of_hosts_" + time.strftime("%Y%m%d_%H%M%S")

        self.num_iterations = num_iterations
        self.total_number_of_hosts = total_number_of_hosts
        self.load_config = load_config
        self.save_config = save_config
        self.controller = controller
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

    def setup_network_graph(self, topo_description):

        controller_port = 6633

        if not self.load_config and self.save_config:
            cm = ControllerMan(1, controller=self.controller)
            controller_port = cm.get_next()

        mm = MininetMan(controller_port, *topo_description)

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

        return ng

    def trigger(self):

        print "Starting experiment..."
        for total_number_of_hosts in self.total_number_of_hosts:

            self.topo_description = ("linear", 2, total_number_of_hosts/2)
            ng = self.setup_network_graph(self.topo_description)

            for i in xrange(self.num_iterations):

                fv = FlowValidator(ng)
                with Timer(verbose=True) as t:
                    fv.init_port_graph()
                self.data["initial_port_graph_construction_time"][total_number_of_hosts].append(t.msecs)

                fv.add_hosts()
                with Timer(verbose=True) as t:
                    fv.initialize_admitted_traffic()

                self.data["initial_traffic_set_propagation_time"][total_number_of_hosts].append(t.msecs)

                fv.validate_all_host_pair_reachability()

        print "Done..."

    def dump_data(self):
        pprint(self.data)
        filename = "data/" + self.experiment_tag + "_data.json"
        print "Writing to file:", filename

        with open(filename, "w") as outfile:
            json.dump(self.data, outfile)


    def plot_number_of_hosts(self):

        initial_port_graph_construction_time = self.data["initial_port_graph_construction_time"]
        h = []

        if initial_port_graph_construction_time:

            x1, \
            initial_port_graph_construction_time_mean, \
            initial_port_graph_construction_time_sem = self.get_x_y_err(initial_port_graph_construction_time)

            l_initial_port_graph_construction_time = plt.errorbar(x1,
                                                                  initial_port_graph_construction_time_mean,
                                                                  initial_port_graph_construction_time_sem,
                                                                  label="Port Graph Construction",
                                                                  fmt="s",
                                                                  color="black")
            h.append(l_initial_port_graph_construction_time)

        plt.xlim((0, 22))
        plt.xticks(range(2, 22, 2), fontsize=16)
        plt.yticks(fontsize=16)

        plt.xlabel("Total number of hosts", fontsize=18)
        plt.ylabel("Port Graph Construction Time(ms)", fontsize=18)
        plt.savefig("plots/" +  self.experiment_tag + "_plot.png")
        plt.show()

    def get_x_y_err(self, data_dict):

        x = sorted(data_dict.keys())

        data_means = []
        data_sems = []

        for p in x:
            mean = np.mean(data_dict[p])
            sem = ss.sem(data_dict[p])
            data_means.append(mean)
            data_sems.append(sem)

        return x, data_means, data_sems

def main():

    num_iterations = 10
    total_number_of_hosts = [2, 4]#, 6, 8, 10]#, 8, 10, 12, 14, 16])#, 18, 20]
    load_config = False
    save_config = True
    controller = "ryu"
    experiment_switches = ["s1", "s2"]

    exp = NumberOfHosts(num_iterations,
                        total_number_of_hosts,
                        load_config,
                        save_config,
                        controller,
                        experiment_switches)

    exp.trigger()
    exp.dump_data()
    exp.plot_number_of_hosts()

if __name__ == "__main__":
    main()