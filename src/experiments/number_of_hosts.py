__author__ = 'Rakesh Kumar'


import sys
sys.path.append("./")
import matplotlib.pyplot as plt

from collections import defaultdict
from timer import Timer
from analysis.flow_validator import FlowValidator
from controller_man import ControllerMan
from experiment import Experiment

class NumberOfHosts(Experiment):

    def __init__(self,
                 num_iterations,
                 total_number_of_hosts,
                 load_config,
                 save_config,
                 controller,
                 experiment_switches):

        super(NumberOfHosts, self).__init__("number_of_hosts",
                                            num_iterations,
                                            load_config,
                                            save_config,
                                            controller,
                                            experiment_switches,
                                            len(total_number_of_hosts))

        self.total_number_of_hosts = total_number_of_hosts

        self.data = {
            "initial_port_graph_construction_time": defaultdict(list),
            "initial_traffic_set_propagation_time": defaultdict(list)
        }

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

                # for (node1, node2) in self.mm.synthesis.primary_path_edges:
                #
                #         fv.port_graph.remove_node_graph_edge(node1, node2)
                #         fv.validate_all_host_pair_reachability()
                #         fv.port_graph.add_node_graph_edge(node1, node2)

                fv.de_init_port_graph()

        print "Done..."

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

def main():

    num_iterations = 1#10
    total_number_of_hosts = [2]#, 6, 8, 10]# 14, 16])#, 18, 20]
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