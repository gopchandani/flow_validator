import sys

from experiment import Experiment
from network_configuration import NetworkConfiguration
from model.traffic import Traffic
from analysis.flow_validator import FlowValidator

__author__ = 'Rakesh Kumar'

sys.path.append("./")


class SynthesisPlayground(Experiment):

    def __init__(self,
                 network_configuration):

        super(SynthesisPlayground, self).__init__("synthesis_playground", 1)

        self.network_configuration = network_configuration

    def trigger(self):

        ng = self.network_configuration.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

        fv = FlowValidator(ng)
        fv.init_network_port_graph()
        fv.add_hosts()
        fv.initialize_admitted_traffic()

        src_zone = [fv.network_graph.get_node_object(h_id).get_switch_port() for h_id in fv.network_graph.host_ids]
        dst_zone = [fv.network_graph.get_node_object(h_id).get_switch_port() for h_id in fv.network_graph.host_ids]

        # src_zone = [fv.network_graph.get_node_object("h11").switch_port]
        # dst_zone = [fv.network_graph.get_node_object("h21").switch_port]

        specific_traffic = Traffic(init_wildcard=True)
        specific_traffic.set_field("ethernet_type", 0x0800)

        connected = fv.validate_zone_pair_connectivity(src_zone, dst_zone, specific_traffic, 0)
        print connected

        connected = fv.validate_zone_pair_connectivity(src_zone, dst_zone, specific_traffic, 1)
        print connected

        print "Done..."


def main():
    # network_configuration = NetworkConfiguration("ryu",
    #                                              "clostopo",
    #                                              {"fanout": 2,
    #                                               "core": 1,
    #                                               "num_hosts_per_switch": 1},
    #                                              load_config=True,
    #                                              save_config=False,
    #                                              synthesis_name="Synthesis_Failover_Aborescene")

    network_configuration = NetworkConfiguration("ryu",
                                                   "ring",
                                                   {"num_switches": 4,
                                                    "num_hosts_per_switch": 1},
                                                   load_config=False,
                                                   save_config=True,
                                                   synthesis_name="Synthesis_Failover_Aborescene")

    exp = SynthesisPlayground(network_configuration)
    exp.trigger()

if __name__ == "__main__":
    main()