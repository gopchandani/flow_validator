__author__ = 'Rakesh Kumar'

import sys
sys.path.append("./")

import matplotlib.pyplot as plt

from collections import defaultdict
from timer import Timer
from analysis.flow_validator import FlowValidator
from experiment import Experiment


class AmerenSetupValidation(Experiment):

    def __init__(self,
                 num_iterations,
                 load_config,
                 save_config,
                 controller,
                 total_number_of_switches_in_ring,
                 total_number_of_ports_to_synthesize):

        super(AmerenSetupValidation, self).__init__("ameren_setup_validation",
                                                           num_iterations,
                                                           load_config,
                                                           save_config,
                                                           controller,
                                                           1)

        self.total_number_of_ports_to_synthesize = total_number_of_ports_to_synthesize
        self.total_number_of_switches_in_ring = total_number_of_switches_in_ring

        self.data = {
            "validation_time": defaultdict(defaultdict),
        }

    def trigger(self):

        print "Starting experiment..."

        for number_of_ports_to_synthesize in xrange(1, self.total_number_of_ports_to_synthesize + 1):
            ports_to_synthesize = xrange(5000, 5000 + number_of_ports_to_synthesize)
            print "ports_to_synthesize:", ports_to_synthesize

            for number_of_switches_in_ring in self.total_number_of_switches_in_ring:
                print "number_of_switches_in_ring:", number_of_switches_in_ring

                self.topo_description = ("amerentopo", number_of_switches_in_ring, 1)

                ng = self.setup_network_graph(self.topo_description,
                                              mininet_setup_gap=number_of_switches_in_ring,
                                              dst_ports_to_synthesize=None,
                                              synthesis_setup_gap=len(ports_to_synthesize),
                                              synthesis_scheme="IntentSynthesis")

                self.data["validation_time"][number_of_ports_to_synthesize][number_of_switches_in_ring] = []

                for i in xrange(self.num_iterations):

                    fv = FlowValidator(ng)
                    fv.init_network_port_graph()
                    fv.add_hosts()
                    fv.initialize_admitted_traffic()

                    with Timer(verbose=True) as t:
                        fv.validate_all_host_pair_backup(verbose=False)

                    self.data["validation_time"][number_of_ports_to_synthesize][number_of_switches_in_ring].append(t.msecs)

                    fv.de_init_network_port_graph()

    def plot_failover_policy_validation_ring(self):

        fig = plt.figure(0)
        self.plot_line_error_bars("validation_time",
                                  "Total number of switches in ring",
                                  "Failover Validation Time (ms)", y_scale="linear")
def main():

    num_iterations = 1
    load_config = True
    save_config = False
    controller = "ryu"

    total_number_of_switches_in_ring = [4]
    total_number_of_ports_to_synthesize = 1

    exp = AmerenSetupValidation(num_iterations,
                                load_config,
                                save_config,
                                controller,
                                total_number_of_switches_in_ring,
                                total_number_of_ports_to_synthesize)

    exp.trigger()
    exp.dump_data()

    #exp.load_data('data/failover_policy_validation_ring_5_iterations_20151206_073212.json')
    #exp.plot_failover_policy_validation_ring()


if __name__ == "__main__":
    main()
