import sys

import matplotlib.pyplot as plt

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

        super(SubstationMixedPolicyValidationTimes, self).__init__("substation_mixed_policy_validation_times", 1)

        self.network_configurations = network_configurations
        self.s1_k_values = s1_k_values
        self.num_iterations = num_iterations

        self.data = {
            "validation_time": defaultdict(defaultdict),
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

        s2_constraints = [PolicyConstraint(CONNECTIVITY_CONSTRAINT, None), PolicyConstraint(PATH_LENGTH_CONSTRAINT, 6)]
        s2_k = 0
        s2 = PolicyStatement(nc.ng, s2_src_zone, s2_dst_zone, s2_traffic, s2_constraints, s2_k)

        return [s1, s2]

    def trigger(self):

        for nc in self.network_configurations:

            print "Configuration:", nc

            fv = FlowValidator(nc.ng)
            fv.init_network_port_graph()

            print "Initialized analysis."

            for s1_k in self.s1_k_values:

                policy_statements = self.construct_policy_statements(nc, s1_k)

                total_host_pairs = (nc.topo_params["num_switches"] * nc.topo_params["num_hosts_per_switch"] *
                                    nc.topo_params["num_switches"] * nc.topo_params["num_hosts_per_switch"])

                sL = str(len(list(nc.ng.get_switch_link_data())))

                self.data["validation_time"]["k: " + str(s1_k) + ", |L|: " + sL][str(total_host_pairs)] = []

                for i in range(self.num_iterations):

                    with Timer(verbose=True) as t:
                        violations = fv.validate_policy(policy_statements)

                    print "Total violations:", len(violations)

                    #self.dump_violations(violations)

                    print "Does the network configuration satisfy the given policy:", (len(violations) == 0)

                    self.data["validation_time"]["k: " + str(s1_k) + ", |L|: " + sL][str(total_host_pairs)].append(t.secs)

                    self.dump_data()

    def plot_data(self):

        f, (ax1) = plt.subplots(1, 1, sharex=True, sharey=False, figsize=(4.5, 4.5))

        data_xtick_labels = self.data["validation_time"]["k: 0, |L|: 4"].keys()
        data_xticks = [int(x) for x in data_xtick_labels]

        self.plot_lines_with_error_bars(ax1,
                                        "validation_time",
                                        "Number of host pairs",
                                        "Time (seconds)",
                                        "",
                                        y_scale='log',
                                        x_min_factor=1.0,
                                        x_max_factor=1.1,
                                        y_min_factor=0.01,
                                        y_max_factor=10,
                                        xticks=data_xticks,
                                        xtick_labels=data_xtick_labels)

        xlabels = ax1.get_xticklabels()
        plt.setp(xlabels, rotation=45, fontsize=10)

        # Shrink current axis's height by 25% on the bottom
        box = ax1.get_position()
        ax1.set_position([box.x0, box.y0 + box.height * 0.3,
                          box.width, box.height * 0.7])

        handles, labels = ax1.get_legend_handles_labels()

        ax1.legend(handles,
                   labels,
                   shadow=True,
                   fontsize=10,
                   loc='upper center',
                   ncol=2,
                   markerscale=1.0,
                   frameon=True,
                   fancybox=True,
                   columnspacing=2.5,
                   bbox_to_anchor=[0.5, -0.20])

        plt.savefig("plots/" + self.experiment_tag + "_substation_mixed_policy_validation_times" + ".png", dpi=1000)
        plt.show()


def prepare_network_configurations(num_switches_in_clique_list, num_hosts_per_switch_list, num_per_switch_links_list):
    nc_list = []

    for nsc in num_switches_in_clique_list:

        for hps in num_hosts_per_switch_list:

            for psl in num_per_switch_links_list:

                nc = NetworkConfiguration("ryu",
                                          "127.0.0.1",
                                          6633,
                                          "http://localhost:8080/",
                                          "admin",
                                          "admin",
                                          "cliquetopo",
                                          {"num_switches": nsc,
                                           "num_hosts_per_switch": hps,
                                           "per_switch_links": psl},#nsc - 1},
                                          conf_root="configurations/",
                                          synthesis_name="AboresceneSynthesis",
                                          synthesis_params={"apply_group_intents_immediately": True})

                nc.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

                nc_list.append(nc)

    return nc_list


def main():

    num_iterations = 1
    num_switches_in_clique_list = [4]#, 5]#, 6]
    num_hosts_per_switch_list = [1]
    num_per_switch_links_list = [2, 3]

    s1_k_values = [3]#, 2, 3, 4]
    network_configurations = prepare_network_configurations(num_switches_in_clique_list,
                                                            num_hosts_per_switch_list,
                                                            num_per_switch_links_list)

    exp = SubstationMixedPolicyValidationTimes(network_configurations, s1_k_values, num_iterations)
    # exp.trigger()
    # exp.dump_data()

    exp.load_data("data/substation_mixed_policy_validation_times_1_iterations_20161214_143932.json")
    exp.plot_data()

if __name__ == "__main__":
    main()
