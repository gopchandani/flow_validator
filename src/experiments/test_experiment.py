__author__ = 'Rakesh Kumar'

import sys

sys.path.append("./")
from analysis.flow_validator import FlowValidator
from experiment import Experiment

class TestExperiment(Experiment):
    def __init__(self,
                 num_iterations,
                 load_config,
                 save_config,
                 controller,
                 fanout,
                 core,
                 total_number_of_ports_to_synthesize):

        super(TestExperiment, self).__init__("test_experiment",
                                         num_iterations,
                                         load_config,
                                         save_config,
                                         controller,
                                         1)

        self.total_number_of_ports_to_synthesize = total_number_of_ports_to_synthesize

        self.fanout = fanout
        self.core = core


    def trigger(self):

        print "Starting experiment..."

        for number_of_ports_to_synthesize in range(1, self.total_number_of_ports_to_synthesize + 1):
            ports_to_synthesize = range(5000, 5000 + number_of_ports_to_synthesize)
            print "ports_to_synthesize:", ports_to_synthesize

            #self.topo_description = ("linear", 2, 1)
            self.topo_description = ("ring", 4, 1, None, None)
            #self.topo_description = ("clostopo", None, 1, self.fanout, self.core)

            ng = self.setup_network_graph(self.topo_description,
                                          mininet_setup_gap=1,
                                          dst_ports_to_synthesize=None,
                                          synthesis_setup_gap=60,
                                          synthesis_scheme="IntentSynthesis")


            self.fv = FlowValidator(ng)
            self.fv.init_network_port_graph()
            self.fv.add_hosts()
            self.fv.initialize_admitted_traffic()

            print "Initialization done."

            analyzed_host_pairs_path_info = self.fv.get_all_host_pairs_traffic_paths()
            all_paths_match = self.compare_host_pair_paths_with_synthesis(analyzed_host_pairs_path_info, verbose=False)
            print "Primary paths TestExperiment, all_paths_match:", all_paths_match

            all_paths_match = self.compare_failover_host_pair_paths_with_synthesis(self.fv, verbose=False)

            print "Failover paths TestExperiment, all_paths_match:", all_paths_match


            self.fv.de_init_network_port_graph()

def main():
    num_iterations = 1#20
    load_config = True
    save_config = False
    controller = "ryu"

    fanout = 2
    core = 1

    total_number_of_ports_to_synthesize = 1

    exp = TestExperiment(num_iterations,
                     load_config,
                     save_config,
                     controller,
                     fanout,
                     core,
                     total_number_of_ports_to_synthesize)

    exp.trigger()


if __name__ == "__main__":
    main()
