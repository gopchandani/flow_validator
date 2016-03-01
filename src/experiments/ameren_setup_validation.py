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
                 controller):

        super(AmerenSetupValidation, self).__init__("ameren_setup_validation",
                                                    num_iterations,
                                                    load_config,
                                                    save_config,
                                                    controller,
                                                    1)

        self.data = {
            "validation_time": defaultdict(list),
        }

    def trigger(self):

        print "Starting experiment..."

        self.topo_description = ("amerentopo", None, None)

        ng = self.setup_network_graph(self.topo_description,
                                      mininet_setup_gap=4,
                                      dst_ports_to_synthesize=None,
                                      synthesis_setup_gap=4,
                                      synthesis_scheme="IntentSynthesis")

        for i in xrange(self.num_iterations):

            fv = FlowValidator(ng)
            fv.init_network_port_graph()
            fv.add_hosts()
            fv.initialize_admitted_traffic()

            with Timer(verbose=True) as t:
                # fv.validate_all_host_pair_backup(['h20', 'h30'],
                #                                  ['h100', '41'],
                #                                  verbose=True)

                fv.validate_host_pair_backup('h20', 'h100', verbose=True)

            self.data["validation_time"][i].append(t.msecs)

            fv.de_init_network_port_graph()

    def plot_failover_policy_validation_ring(self):

        fig = plt.figure(0)
        self.plot_line_error_bars("validation_time",
                                  "Ameren Setup",
                                  "Failover Validation Time (ms)", y_scale="linear")
def main():

    num_iterations = 1
    load_config = False
    save_config = True
    controller = "ryu"

    exp = AmerenSetupValidation(num_iterations,
                                load_config,
                                save_config,
                                controller)

    exp.trigger()
    exp.dump_data()

    #exp.load_data('data/failover_policy_validation_ring_5_iterations_20151206_073212.json')
    #exp.plot_failover_policy_validation_ring()


if __name__ == "__main__":
    main()
