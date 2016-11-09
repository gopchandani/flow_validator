import sys

from collections import defaultdict

from timer import Timer
from experiment import Experiment
from network_configuration import NetworkConfiguration
from model.traffic import Traffic
from analysis.flow_validator import FlowValidator

__author__ = 'Rakesh Kumar'

sys.path.append("./")

from analysis.policy_statement import PolicyStatement

class SubstationMixedPolicyValidationTimes(Experiment):

    def __init__(self,
                 network_configuration,
                 num_iterations):

        super(SubstationMixedPolicyValidationTimes, self).__init__("resiliency_policy_times", 1)

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

                s1_src_zone = [fv.network_graph.get_node_object("h11").switch_port]

                s1_dst_zone = [fv.network_graph.get_node_object("h21").switch_port,
                               fv.network_graph.get_node_object("h31").switch_port]

                s1_traffic = Traffic(init_wildcard=True)
                s1_traffic.set_field("ethernet_type", 0x0800)
                s1_traffic.set_field("vlan_id", 1 + 0x1000)
                s1_traffic.set_field("has_vlan_tag", 1)

                s1_constraints = ["Connectivity"]
                s1_k = 1
                s1 = PolicyStatement(s1_src_zone, s1_dst_zone, s1_traffic, s1_constraints, s1_k)

                connected = fv.validate_zone_pair_connectivity(sw1_zone, sw1_zone, s1_traffic, 0)
                print "s1:", connected

            self.data["validation_time"][self.network_configuration.nc_topo_str].append(t.secs)


def main():

    num_iterations = 2

    network_configuration = NetworkConfiguration("ryu",
                                                 "127.0.0.1",
                                                 6633,
                                                 "http://localhost:8080/",
                                                 "admin",
                                                 "admin",
                                                 "cliquetopo",
                                                 {"num_switches": 4,
                                                  "num_hosts_per_switch": 1,
                                                  "per_switch_links": 3},
                                                 conf_root="configurations/",
                                                 synthesis_name="AboresceneSynthesis",
                                                 synthesis_params={"apply_group_intents_immediately": True})

    exp = SubstationMixedPolicyValidationTimes(network_configuration, num_iterations)
    exp.trigger()
    exp.dump_data()

if __name__ == "__main__":
    main()
