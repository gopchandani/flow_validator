__author__ = 'Rakesh Kumar'


import sys
sys.path.append("./")
import matplotlib.pyplot as plt

from collections import defaultdict
from timer import Timer
from analysis.flow_validator import FlowValidator
from experiment import Experiment

class InitializationTimes(Experiment):

    def __init__(self,
                 num_iterations,
                 total_number_of_hosts,
                 total_number_of_ports_to_synthesize,
                 load_config,
                 save_config,
                 controller):

        super(InitializationTimes, self).__init__("initialization_times",
                                                  num_iterations,
                                                  load_config,
                                                  save_config,
                                                  controller,
                                                  len(total_number_of_hosts))

        self.total_number_of_hosts = total_number_of_hosts
        self.total_number_of_ports_to_synthesize = total_number_of_ports_to_synthesize

        self.data = {
            "construction_time": defaultdict(defaultdict),
            "propagation_time": defaultdict(defaultdict),
        }

    def trigger(self):

        print "Starting experiment..."

        for number_of_ports_to_synthesize in range(1, self.total_number_of_ports_to_synthesize + 1):
            ports_to_synthesize = range(5000, 5000 + number_of_ports_to_synthesize)
            print "ports_to_synthesize:", ports_to_synthesize

            for total_number_of_hosts in self.total_number_of_hosts:
                print "total_number_of_hosts:", total_number_of_hosts

                self.topo_description = ("linear", 2, total_number_of_hosts/2)

                ng = self.setup_network_graph(self.topo_description,
                                              mininet_setup_gap=total_number_of_hosts,
                                              dst_ports_to_synthesize=ports_to_synthesize,
                                              synthesis_setup_gap=len(ports_to_synthesize))

                self.data["construction_time"][number_of_ports_to_synthesize][total_number_of_hosts] = []
                self.data["propagation_time"][number_of_ports_to_synthesize][total_number_of_hosts] = []

                for i in xrange(self.num_iterations):

                    fv = FlowValidator(ng)
                    with Timer(verbose=True) as t:
                        fv.init_network_port_graph()

                    self.data["construction_time"][number_of_ports_to_synthesize][total_number_of_hosts].append(t.msecs)

                    fv.add_hosts()
                    with Timer(verbose=True) as t:
                        fv.initialize_admitted_traffic()

                    self.data["propagation_time"][number_of_ports_to_synthesize][total_number_of_hosts].append(t.msecs)
                    fv.validate_all_host_pair_reachability(verbose=False)

                    fv.de_init_network_port_graph()

        print "Done..."

    def plot_initialization_times(self):

        fig = plt.figure(0)
        self.plot_line_error_bars("construction_time",
                                  "Total number of hosts",
                                  "Port Graph Construction Time (ms)")

        fig = plt.figure(1)
        self.plot_line_error_bars("propagation_time",
                                  "Total number of hosts",
                                  "Admitted Traffic Propagation Time (ms)")
def main():

    num_iterations = 5
    total_number_of_hosts = [2, 4, 6, 8]
    total_number_of_ports_to_synthesize = 3
    load_config = False
    save_config = True
    controller = "ryu"

    exp = InitializationTimes(num_iterations,
                              total_number_of_hosts,
                              total_number_of_ports_to_synthesize,
                              load_config,
                              save_config,
                              controller)

    exp.trigger()
    exp.dump_data()

    #exp.load_data('data/play_data_init_time.json')

    exp.plot_initialization_times()

if __name__ == "__main__":
    main()