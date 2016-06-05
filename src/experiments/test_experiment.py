__author__ = 'Rakesh Kumar'

import sys

sys.path.append("./")

from analysis.flow_validator import FlowValidator
from experiment import Experiment
from network_configuration import NetworkConfiguration


class TestExperiment(Experiment):
    def __init__(self,
                 num_iterations,
                 load_config,
                 save_config,
                 controller,
                 network_configurations):

        super(TestExperiment, self).__init__("test_experiment",
                                             num_iterations,
                                             load_config,
                                             save_config,
                                             controller,
                                             1)

        self.network_configurations = network_configurations

    def trigger(self):

        print "Starting experiment..."

        for network_configuration in self.network_configurations:

            topo_description = (network_configuration.topo_name,
                                network_configuration.num_switches,
                                network_configuration.num_hosts_per_switch,
                                network_configuration.fanout,
                                network_configuration.core)

            ng = self.setup_network_graph(topo_description,
                                          mininet_setup_gap=5,
                                          dst_ports_to_synthesize=None,
                                          synthesis_setup_gap=10,
                                          synthesis_scheme="IntentSynthesis")

            self.fv = FlowValidator(ng, True)
            self.fv.init_network_port_graph()
            self.fv.add_hosts()
            self.fv.initialize_admitted_traffic()

            print "Initialization done."

            analyzed_host_pairs_path_info = self.fv.get_all_host_pairs_traffic_paths()

            all_paths_match = self.compare_primary_paths_with_synthesis(self.fv,
                                                                        analyzed_host_pairs_path_info,
                                                                        verbose=False)

            print "Primary paths TestExperiment, all_paths_match:", all_paths_match

            all_paths_match = self.compare_failover_paths_with_synthesis(self.fv,
                                                                         self.fv.network_graph.graph.edges(),
                                                                         #links_to_try=[("s3", "s2")],
                                                                         verbose=False)

            print "Failover paths TestExperiment, all_paths_match:", all_paths_match

            self.fv.de_init_network_port_graph()


def main():
    num_iterations = 1#20
    load_config = False
    save_config = True
    controller = "ryu"

    #network_configurations = [NetworkConfiguration("clostopo", 7, 1, 2, 1)]

    network_configurations = [NetworkConfiguration("clostopo", 7, 1, 2, 1),
                              NetworkConfiguration("ring", 4, 1, None, None)]

    exp = TestExperiment(num_iterations,
                         load_config,
                         save_config,
                         controller,
                         network_configurations)

    exp.trigger()


if __name__ == "__main__":
    main()
