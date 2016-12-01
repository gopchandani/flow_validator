import sys

from collections import defaultdict

from timer import Timer
from experiment import Experiment
from network_configuration import NetworkConfiguration
from model.traffic import Traffic
from analysis.flow_validator import FlowValidator

__author__ = 'Rakesh Kumar'

sys.path.append("./")

from analysis.policy_statement import PolicyStatement, PolicyConstraint
from analysis.policy_statement import CONNECTIVITY_CONSTRAINT, PATH_LENGTH_CONSTRAINT, LINK_EXCLUSIVITY_CONSTRAINT


class SubstationMixedPolicyValidationTimes(Experiment):

    def __init__(self,
                 network_configurations,
                 s1_k_values,
                 num_iterations):

        super(SubstationMixedPolicyValidationTimes, self).__init__("resiliency_policy_times", 1)

        self.network_configurations = network_configurations
        self.s1_k_values = s1_k_values
        self.num_iterations = num_iterations

        self.data = {
            "validation_time": defaultdict(defaultdict)
        }

    def construct_policy_statements(self, nc, s1_k):

        s1_src_zone = [nc.ng.get_node_object("h21").switch_port,
                       nc.ng.get_node_object("h31").switch_port]

        s1_dst_zone = [nc.ng.get_node_object("h11").switch_port]

        s1_traffic = Traffic(init_wildcard=True)
        s1_traffic.set_field("ethernet_type", 0x0800)
        s1_traffic.set_field("has_vlan_tag", 0)

        s1_constraints = [PolicyConstraint(CONNECTIVITY_CONSTRAINT, None),
                          PolicyConstraint(PATH_LENGTH_CONSTRAINT, 6),
                          PolicyConstraint(LINK_EXCLUSIVITY_CONSTRAINT, [("s1", "s2")])]

        s1 = PolicyStatement(nc.ng, s1_src_zone, s1_dst_zone, s1_traffic, s1_constraints, s1_k)

        s2_src_zone = [nc.ng.get_node_object("h41").switch_port]

        s2_dst_zone = [nc.ng.get_node_object("h11").switch_port]

        s2_traffic = Traffic(init_wildcard=True)
        s2_traffic.set_field("ethernet_type", 0x0800)
        s2_traffic.set_field("has_vlan_tag", 0)
        s2_traffic.set_field("tcp_destination_port", 443)

        s2_constraints = [PolicyConstraint(CONNECTIVITY_CONSTRAINT, None)]
        s2_k = 0
        s2 = PolicyStatement(nc.ng, s2_src_zone, s2_dst_zone, s2_traffic, s2_constraints, s2_k)

        return [s1, s2]

    def trigger(self):

        for nc in self.network_configurations:
            for s1_k in self.s1_k_values:

                for i in range(self.num_iterations):

                    policy_statements = self.construct_policy_statements(nc, s1_k)

                    total_host_pairs = (nc.topo_params["num_switches"] * nc.topo_params["num_hosts_per_switch"] *
                                        nc.topo_params["num_switches"] * nc.topo_params["num_hosts_per_switch"])

                    self.data["validation_time"][str(s1_k)][str(total_host_pairs)] = []

                    with Timer(verbose=True) as t:
                        fv = FlowValidator(nc.ng)
                        fv.init_network_port_graph()
                        satisfies = fv.validate_policy(policy_statements)

                    print "Does the network configuration satisfies the given policy:", satisfies

                    self.data["validation_time"][str(s1_k)][str(total_host_pairs)].append(t.secs)


def prepare_network_configurations(num_switches_in_clique_list, num_hosts_per_switch_list):
    nc_list = []

    for nsc in num_switches_in_clique_list:

        for hps in num_hosts_per_switch_list:

            nc = NetworkConfiguration("ryu",
                                      "127.0.0.1",
                                      6633,
                                      "http://localhost:8080/",
                                      "admin",
                                      "admin",
                                      "cliquetopo",
                                      {"num_switches": nsc,
                                       "num_hosts_per_switch": hps,
                                       "per_switch_links": nsc - 1},
                                      conf_root="configurations/",
                                      synthesis_name="AboresceneSynthesis",
                                      synthesis_params={"apply_group_intents_immediately": True})

            nc.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

            nc_list.append(nc)

    return nc_list


def main():

    num_iterations = 1

    num_switches_in_clique_list = [4]
    num_hosts_per_switch_list = [1]
    s1_k_values = [1, 2]

    network_configurations = prepare_network_configurations(num_switches_in_clique_list, num_hosts_per_switch_list)

    exp = SubstationMixedPolicyValidationTimes(network_configurations, s1_k_values, num_iterations)
    exp.trigger()
    exp.dump_data()

if __name__ == "__main__":
    main()
