import sys

from collections import defaultdict

from timer import Timer
from experiment import Experiment
from network_configuration import NetworkConfiguration
from model.traffic import Traffic
from analysis.flow_validator import FlowValidator

__author__ = 'Rakesh Kumar'

sys.path.append("./")


class SecurityPolicyTimes(Experiment):

    def __init__(self,
                 network_configuration,
                 num_iterations):

        super(SecurityPolicyTimes, self).__init__("security_policy_times", 1)

        self.network_configuration = network_configuration
        self.num_iterations = num_iterations

        self.data = {
            "validation_time": defaultdict(list)
        }

    def trigger(self):

        ng = self.network_configuration.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

        for i in range(self.num_iterations):

            with Timer(verbose=True) as t:

                fv = FlowValidator(ng)
                fv.init_network_port_graph()

                control_zone = [fv.network_graph.get_node_object("h11").switch_port,
                                fv.network_graph.get_node_object("h21").switch_port,
                                fv.network_graph.get_node_object("h31").switch_port]

                control_specific_traffic = Traffic(init_wildcard=True)
                control_specific_traffic.set_field("ethernet_type", 0x0800)
                control_specific_traffic.set_field("vlan_id", 255 + 0x1000)
                control_specific_traffic.set_field("has_vlan_tag", 1)
                control_specific_traffic.set_field("tcp_source_port", 80)
                control_specific_traffic.set_field("tcp_destination_port", 80)

                connected = fv.validate_zone_pair_connectivity(control_zone, control_zone, control_specific_traffic, 0)
                print "control_zone:", connected

                # cross_vlan_traffic = Traffic(init_wildcard=True)
                # cross_vlan_traffic.set_field("ethernet_type", 0x0800)
                # cross_vlan_traffic.set_field("vlan_id", 250 + 0x1000)
                # cross_vlan_traffic.set_field("has_vlan_tag", 1)
                #
                # connected = fv.validate_zone_pair_connectivity(sw1_zone, sw2_zone, cross_vlan_traffic, 0)
                # print "sw1_zone -> sw2_zone:", connected

            self.data["validation_time"][self.network_configuration.nc_topo_str].append(t.secs)


def main():

    num_iterations = 2

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

    exp = SecurityPolicyTimes(network_configuration, num_iterations)
    exp.trigger()
    exp.dump_data()

if __name__ == "__main__":
    main()
