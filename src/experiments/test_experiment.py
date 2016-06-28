__author__ = 'Rakesh Kumar'

import sys

sys.path.append("./")

from analysis.flow_validator import FlowValidator
from experiment import Experiment
from network_configuration import NetworkConfiguration


class TestExperiment(Experiment):
    def __init__(self,
                 num_iterations,
                 network_configurations):

        super(TestExperiment, self).__init__("test_experiment",
                                             num_iterations)

        self.network_configurations = network_configurations

    def trigger(self):

        print "Starting experiment..."

        for network_configuration in self.network_configurations:

            ng = network_configuration.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

            fv = FlowValidator(ng, True)
            fv.init_network_port_graph()
            fv.add_hosts()
            fv.initialize_admitted_traffic()

            print "Initialization done."

            analyzed_host_pairs_path_info = fv.get_all_host_pairs_traffic_paths()

            all_paths_match = self.compare_primary_paths_with_synthesis(fv,
                                                                        network_configuration,
                                                                        analyzed_host_pairs_path_info,
                                                                        verbose=False)

            print "Primary paths TestExperiment, all_paths_match:", all_paths_match

            all_paths_match = self.compare_failover_paths_with_synthesis(fv,
                                                                         network_configuration,
                                                                         fv.network_graph.graph.edges(),
                                                                         #links_to_try=[("s3", "s2")],
                                                                         verbose=False)

            print "Failover paths TestExperiment, all_paths_match:", all_paths_match

            fv.de_init_network_port_graph()


def main():
    num_iterations = 1#20

    # network_configurations = [NetworkConfiguration("ryu",
    #                                                "clostopo",
    #                                                {"fanout": 2,
    #                                                 "core": 1,
    #                                                 "num_hosts_per_switch": 1},
    #                                                load_config=False,
    #                                                save_config=True,
    #                                                synthesis_name="DijkstraSynthesis")]
    # #
    network_configurations = [NetworkConfiguration("ryu",
                                                   "ring",
                                                   {"num_switches": 4,
                                                    "num_hosts_per_switch": 1},
                                                   load_config=False,
                                                   save_config=True,
                                                   synthesis_name="DijkstraSynthesis")]


    exp = TestExperiment(num_iterations,
                         network_configurations)

    exp.trigger()


if __name__ == "__main__":
    main()
