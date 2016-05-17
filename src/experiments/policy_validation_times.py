__author__ = 'Rakesh Kumar'

import sys

sys.path.append("./")

import matplotlib.pyplot as plt

from collections import defaultdict
from timer import Timer
from analysis.flow_validator import FlowValidator
from experiment import Experiment

from model.traffic import Traffic


class PolicyValidationTimes(Experiment):

    def __init__(self,
                 num_iterations,
                 load_config,
                 save_config,
                 controller,
                 total_number_of_switches_in_ring):

        super(PolicyValidationTimes, self).__init__("policy_validation_times",
                                                    num_iterations,
                                                    load_config,
                                                    save_config,
                                                    controller,
                                                    1)

        self.total_number_of_switches_in_ring = total_number_of_switches_in_ring

        self.data = {
            "validation_time": defaultdict(defaultdict),
        }

    def trigger(self):

        print "Starting experiment..."

        for number_of_switches_in_ring in self.total_number_of_switches_in_ring:
            print "number_of_switches_in_ring:", number_of_switches_in_ring

            self.topo_description = ("ring", number_of_switches_in_ring, 1)

            ng = self.setup_network_graph(self.topo_description,
                                          mininet_setup_gap=number_of_switches_in_ring,
                                          dst_ports_to_synthesize=None,
                                          synthesis_setup_gap=5,
                                          synthesis_scheme="IntentSynthesis")

            for i in xrange(self.num_iterations):

                fv = FlowValidator(ng)
                fv.init_network_port_graph()
                fv.add_hosts()
                fv.initialize_admitted_traffic()

                src_zone = [fv.network_graph.get_node_object(h_id).get_switch_port() for h_id in fv.network_graph.host_ids]
                dst_zone = [fv.network_graph.get_node_object(h_id).get_switch_port() for h_id in fv.network_graph.host_ids]

                specific_traffic = Traffic(init_wildcard=True)
                specific_traffic.set_field("ethernet_type", 0x0800)

                with Timer(verbose=True) as t:
                    connected = fv.validate_zone_pair_connectivity(src_zone, dst_zone, specific_traffic, 1)
                    print connected

                with Timer(verbose=True) as t:
                    within_limit = fv.validate_zone_pair_path_length(src_zone, dst_zone, specific_traffic, 6, 1)
                    print within_limit

                with Timer(verbose=True) as t:
                    el = [self.ng.get_link_data('s3', 's4')]
                    is_exclusive = fv.validate_zone_pair_link_exclusivity(src_zone, dst_zone, specific_traffic, el, 1)
                    print is_exclusive

                fv.de_init_network_port_graph()

    def plot_policy_validation_times(self):

        fig = plt.figure(0)
        self.plot_line_error_bars("validation_time",
                                  "Total number of switches in ring",
                                  "Failover Validation Time (ms)", y_scale="linear")

def main():

    num_iterations = 1
    load_config = True
    save_config = False
    controller = "ryu"

    total_number_of_switches_in_ring = [4] #3, 4, 5, 6, 7, 8, 9, 10]

    exp = PolicyValidationTimes(num_iterations,
                                load_config,
                                save_config,
                                controller,
                                total_number_of_switches_in_ring)

    exp.trigger()
    exp.dump_data()

    #exp.load_data('data/policy_validation_times_5_iterations_20151206_073212.json')
    #exp.plot_policy_validation_times()


if __name__ == "__main__":
    main()
