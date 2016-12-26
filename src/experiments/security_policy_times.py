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
from analysis.policy_statement import CONNECTIVITY_CONSTRAINT, ISOLATION_CONSTRAINT


class SecurityPolicyTimes(Experiment):

    def __init__(self,
                 nc_list,
                 num_iterations):

        super(SecurityPolicyTimes, self).__init__("security_policy_times", 1)

        self.nc_list = nc_list
        self.num_iterations = num_iterations

        self.data = {
            "initialization_time": defaultdict(defaultdict),
            "validation_time": defaultdict(defaultdict)
        }

    def construct_policy_statements(self, nc):
        statements = []
        enclave_zones_traffic_tuples = []
        control_zone = []
        non_control_zone = []
        control_vlan_id = 255

        all_switches = sorted(list(nc.ng.get_switches()), key=lambda x: int(x.node_id[1:]))
        for sw in all_switches[0:len(all_switches) - 1]:

            enclave_zone = []
            for port_num in sw.host_ports:
                enclave_zone.append(sw.ports[port_num])

                if port_num == 1:
                    control_zone.append(sw.ports[port_num])
                else:
                    non_control_zone.append(sw.ports[port_num])

            enclave_specific_traffic = Traffic(init_wildcard=True)
            enclave_specific_traffic.set_field("ethernet_type", 0x0800)
            enclave_specific_traffic.set_field("vlan_id", int(sw.node_id[1:]) + 0x1000)
            enclave_specific_traffic.set_field("has_vlan_tag", 1)

            enclave_zones_traffic_tuples.append((enclave_zone, enclave_specific_traffic))

        for src_enclave_zone, src_enclave_specific_traffic in enclave_zones_traffic_tuples:
            for dst_enclave_zone, dst_enclave_specific_traffic in enclave_zones_traffic_tuples:
                if src_enclave_zone == dst_enclave_zone:

                    enclave_constraints = [PolicyConstraint(CONNECTIVITY_CONSTRAINT, None)]

                    enclave_statement = PolicyStatement(nc.ng,
                                                        src_enclave_zone,
                                                        dst_enclave_zone,
                                                        src_enclave_specific_traffic,
                                                        enclave_constraints, 0)

                    statements.append(enclave_statement)
                else:
                    enclave_constraints = [PolicyConstraint(ISOLATION_CONSTRAINT, None)]

                    enclave_statement = PolicyStatement(nc.ng,
                                                        src_enclave_zone,
                                                        dst_enclave_zone,
                                                        src_enclave_specific_traffic,
                                                        enclave_constraints, 0)

                    statements.append(enclave_statement)

        control_switch = all_switches[len(all_switches) - 1]
        control_zone.append(nc.ng.get_node_object("h" + control_switch.node_id[1:] + "1").switch_port)

        control_enclave_specific_traffic = Traffic(init_wildcard=True)
        control_enclave_specific_traffic.set_field("ethernet_type", 0x0800)
        control_enclave_specific_traffic.set_field("vlan_id", control_vlan_id + 0x1000)
        control_enclave_specific_traffic.set_field("has_vlan_tag", 1)

        enclave_constraints = [PolicyConstraint(CONNECTIVITY_CONSTRAINT, None)]
        enclave_statement = PolicyStatement(nc.ng,
                                            control_zone,
                                            control_zone,
                                            control_enclave_specific_traffic,
                                            enclave_constraints, 0)
        statements.append(enclave_statement)

        enclave_constraints = [PolicyConstraint(ISOLATION_CONSTRAINT, None)]
        enclave_statement = PolicyStatement(nc.ng,
                                            control_zone,
                                            non_control_zone,
                                            control_enclave_specific_traffic,
                                            enclave_constraints, 0)
        statements.append(enclave_statement)

        enclave_constraints = [PolicyConstraint(ISOLATION_CONSTRAINT, None)]
        enclave_statement = PolicyStatement(nc.ng,
                                            non_control_zone,
                                            control_zone,
                                            control_enclave_specific_traffic,
                                            enclave_constraints, 0)
        statements.append(enclave_statement)

        return statements

    def trigger(self):

        for nc in self.nc_list:

            with Timer(verbose=True) as t:
                fv = FlowValidator(nc.ng)
                fv.init_network_port_graph()

            self.dump_data()

            policy_statements = self.construct_policy_statements(nc)
            print "Total statements:", len(policy_statements)

            policy_len_str = "# Policy Statements:" + str(len(policy_statements))

            self.data["initialization_time"][policy_len_str][nc.topo_params["nHostsPerSwitch"]] = []
            self.data["validation_time"][policy_len_str][nc.topo_params["nHostsPerSwitch"]] = []

            self.data["initialization_time"][policy_len_str][nc.topo_params["nHostsPerSwitch"]].append(t.secs)

            for i in range(self.num_iterations):
                with Timer(verbose=True) as t:
                    violations = fv.validate_policy(policy_statements)

                self.data["validation_time"][policy_len_str][nc.topo_params["nHostsPerSwitch"]].append(t.secs)
                self.dump_data()
                print "Total violations:", len(violations)


def prepare_network_configurations(num_grids_list, num_hosts_per_switch_list):

    nc_list = []
    num_switches_per_grid = 3

    for num_grids in num_grids_list:

        for num_hosts_per_switch in num_hosts_per_switch_list:

            ip_str = "172.17.0.140"
            port_str = "8181"

            nc = NetworkConfiguration("onos",
                                      ip_str,
                                      int(port_str),
                                      "http://" + ip_str + ":" + port_str + "/onos/v1/",
                                      "karaf",
                                      "karaf",
                                      "microgrid_topo",
                                      {"num_switches": 1 + num_grids * num_switches_per_grid,
                                       "nGrids": num_grids,
                                       "nSwitchesPerGrid": num_switches_per_grid,
                                       "nHostsPerSwitch": num_hosts_per_switch},
                                      conf_root="configurations/",
                                      synthesis_name=None,
                                      synthesis_params=None)

            nc.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

            nc_list.append(nc)

    return nc_list


def main():

    num_iterations = 3
    num_grids_list = [1]#, 2, 3]#, 4, 5]
    num_hosts_per_switch_list = [3]#[3, 4, 5]

    nc_list = prepare_network_configurations(num_grids_list, num_hosts_per_switch_list)

    exp = SecurityPolicyTimes(nc_list, num_iterations)
    exp.trigger()
    exp.dump_data()

if __name__ == "__main__":
    main()
