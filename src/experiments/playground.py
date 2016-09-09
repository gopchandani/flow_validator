import sys

from experiment import Experiment
from network_configuration import NetworkConfiguration
from model.traffic import Traffic
from analysis.flow_validator import FlowValidator

__author__ = 'Rakesh Kumar'

sys.path.append("./")


class Playground(Experiment):

    def __init__(self,
                 network_configuration):

        super(Playground, self).__init__("playground", 1)

        self.network_configuration = network_configuration

    def trigger(self):

        ng = self.network_configuration.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

        fv = FlowValidator(ng)
        fv.init_network_port_graph()

        src_zone = [fv.network_graph.get_node_object(h_id).switch_port for h_id in fv.network_graph.host_ids]
        dst_zone = [fv.network_graph.get_node_object(h_id).switch_port for h_id in fv.network_graph.host_ids]

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

    network_configuration = NetworkConfiguration("onos",
                                                 "10.0.2.15",
                                                 6653,
                                                 "http://10.0.2.15:8181/onos/v1/",
                                                 "karaf",
                                                 "karaf",
                                                 "clostopo",
                                                 {"fanout": 2,
                                                  "core": 1,
                                                  "num_hosts_per_switch": 1},
                                                 conf_root="configurations/",
                                                 synthesis_name="AboresceneSynthesis",
                                                 synthesis_params={"apply_group_intents_immediately": True})

    # network_configuration = NetworkConfiguration("onos",
    #                                              "10.0.2.15",
    #                                              6653,
    #                                              "http://10.0.2.15:8181/onos/v1/",
    #                                              "karaf",
    #                                              "karaf",
    #                                              "clostopo",
    #                                              {"fanout": 2,
    #                                               "core": 1,
    #                                               "num_hosts_per_switch": 1},
    #                                              conf_root="configurations/",
    #                                              synthesis_name="AboresceneSynthesis",
    #                                              synthesis_params={"apply_group_intents_immediately": True})

    # network_configuration = NetworkConfiguration("ryu",
    #                                              "127.0.0.1",
    #                                              6633,
    #                                              "http://localhost:8080/",
    #                                              "admin",
    #                                              "admin",
    #                                              "ring",
    #                                              {"num_switches": 4,
    #                                               "num_hosts_per_switch": 1},
    #                                              conf_root="configurations/",
    #                                              synthesis_name="AboresceneSynthesis",
    #                                              synthesis_params={"apply_group_intents_immediately": True})

    # network_configuration = NetworkConfiguration("sel",
    #                                              "192.168.56.101",
    #                                              6653,
    #                                              "https://192.168.56.101:443/",
    #                                              "hobbs",
    #                                              "Asdf123$",
    #                                              "linear",
    #                                              {"num_switches": 2,
    #                                               "num_hosts_per_switch": 1},
    #                                              conf_root="configurations/",
    #                                              synthesis_name="DijkstraSynthesis",
    #                                              synthesis_params={"apply_group_intents_immediately": True})

    exp = Playground(network_configuration)
    exp.trigger()

if __name__ == "__main__":
    main()