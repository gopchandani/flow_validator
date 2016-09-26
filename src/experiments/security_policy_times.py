import sys

from experiment import Experiment
from network_configuration import NetworkConfiguration
from model.traffic import Traffic
from analysis.flow_validator import FlowValidator

__author__ = 'Rakesh Kumar'

sys.path.append("./")


class SecurityPolicyTimes(Experiment):

    def __init__(self,
                 network_configuration):

        super(SecurityPolicyTimes, self).__init__("security_policy_times", 1)

        self.network_configuration = network_configuration

    def trigger(self):

        ng = self.network_configuration.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

        fv = FlowValidator(ng)
        fv.init_network_port_graph()

        sw1_zone = [fv.network_graph.get_node_object("h11").switch_port,
                    fv.network_graph.get_node_object("h12").switch_port,
                    fv.network_graph.get_node_object("h13").switch_port]

        s1_specific_traffic = Traffic(init_wildcard=True)
        s1_specific_traffic.set_field("ethernet_type", 0x0800)
        s1_specific_traffic.set_field("vlan_id", 100 + 0x1000)
        s1_specific_traffic.set_field("has_vlan_tag", 1)

        connected = fv.validate_zone_pair_connectivity(sw1_zone, sw1_zone, s1_specific_traffic, 0)
        print "s1:", connected

        sw2_zone = [fv.network_graph.get_node_object("h21").switch_port,
                    fv.network_graph.get_node_object("h22").switch_port,
                    fv.network_graph.get_node_object("h23").switch_port]

        s2_specific_traffic = Traffic(init_wildcard=True)
        s2_specific_traffic.set_field("ethernet_type", 0x0800)
        s2_specific_traffic.set_field("vlan_id", 200 + 0x1000)
        s2_specific_traffic.set_field("has_vlan_tag", 1)

        connected = fv.validate_zone_pair_connectivity(sw2_zone, sw2_zone, s2_specific_traffic, 0)
        print "s2:", connected

        sw3_zone = [fv.network_graph.get_node_object("h31").switch_port,
                    fv.network_graph.get_node_object("h32").switch_port,
                    fv.network_graph.get_node_object("h33").switch_port]

        s3_specific_traffic = Traffic(init_wildcard=True)
        s3_specific_traffic.set_field("ethernet_type", 0x0800)
        s3_specific_traffic.set_field("vlan_id", 250 + 0x1000)
        s3_specific_traffic.set_field("has_vlan_tag", 1)

        connected = fv.validate_zone_pair_connectivity(sw3_zone, sw3_zone, s3_specific_traffic, 0)
        print "s3:", connected

        control_zone = [fv.network_graph.get_node_object("h11").switch_port,
                        fv.network_graph.get_node_object("h21").switch_port,
                        fv.network_graph.get_node_object("h31").switch_port]

        control_specific_traffic = Traffic(init_wildcard=True)
        control_specific_traffic.set_field("ethernet_type", 0x0800)
        control_specific_traffic.set_field("vlan_id", 150 + 0x1000)
        control_specific_traffic.set_field("has_vlan_tag", 1)

        connected = fv.validate_zone_pair_connectivity(control_zone, control_zone, control_specific_traffic, 0)
        print "control_zone:", connected

        cross_vlan_traffic = Traffic(init_wildcard=True)
        cross_vlan_traffic.set_field("ethernet_type", 0x0800)
        cross_vlan_traffic.set_field("vlan_id", 250 + 0x1000)
        cross_vlan_traffic.set_field("has_vlan_tag", 1)

        connected = fv.validate_zone_pair_connectivity(sw1_zone, sw2_zone, cross_vlan_traffic, 0)
        print "sw1_zone -> sw2_zone:", connected


def main():

    network_configuration = NetworkConfiguration("onos",
                                                 "72.36.82.150",
                                                 40002,
                                                 "http://72.36.82.150:40001/onos/v1/",
                                                 "karaf",
                                                 "karaf",
                                                 "clostopo",
                                                 {"fanout": 2,
                                                  "core": 1,
                                                  "num_hosts_per_switch": 1},
                                                 conf_root="configurations/",
                                                 synthesis_name=None,
                                                 synthesis_params=None)

    exp = SecurityPolicyTimes(network_configuration)
    exp.trigger()

if __name__ == "__main__":
    main()
