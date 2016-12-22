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


class SecurityPolicyTimes(Experiment):

    def __init__(self,
                 nc_list,
                 num_iterations):

        super(SecurityPolicyTimes, self).__init__("security_policy_times", 1)

        self.nc_list = nc_list
        self.num_iterations = num_iterations

        self.data = {
            "validation_time": defaultdict(list)
        }

    def construct_policy_statements(self, nc):

        control_zone = [nc.ng.get_node_object("h11").switch_port,
                        nc.ng.get_node_object("h21").switch_port,
                        nc.ng.get_node_object("h31").switch_port]

        control_specific_traffic = Traffic(init_wildcard=True)
        control_specific_traffic.set_field("ethernet_type", 0x0800)
        control_specific_traffic.set_field("vlan_id", 255 + 0x1000)
        control_specific_traffic.set_field("has_vlan_tag", 1)
        control_specific_traffic.set_field("tcp_source_port", 80)
        control_specific_traffic.set_field("tcp_destination_port", 80)

        control_constraints = [PolicyConstraint(CONNECTIVITY_CONSTRAINT, None)]
        control_s = PolicyStatement(nc.ng,
                                    control_zone,
                                    control_zone,
                                    control_specific_traffic,
                                    control_constraints, 0)

        return [control_s]

    def trigger(self):

        for i in range(self.num_iterations):

            nc = self.nc_list[0]

            with Timer(verbose=True) as t:

                fv = FlowValidator(self.nc_list[0].ng)
                fv.init_network_port_graph()

                policy_statements = self.construct_policy_statements(nc)
                violations = fv.validate_policy(policy_statements)
                print "violations:", violations

            self.data["validation_time"][nc.nc_topo_str].append(t.secs)


def prepare_network_configurations(num_grids_list):

    nc_list = []
    num_switches_per_grid = 3
    num_hosts_per_switch = 3

    for num_grids in num_grids_list:
        nc = NetworkConfiguration("onos",
                                  "172.17.0.94",
                                  8181,
                                  "http://172.17.0.94:8181/onos/v1/",
                                  "karaf",
                                  "karaf",
                                  "microgrid_topo",
                                  {"num_switches": 1 + num_grids * num_switches_per_grid,
                                   "nGrids": num_grids,
                                   "nSwitchesPerGrid": num_switches_per_grid,
                                   "nHostsPerSwitch": num_hosts_per_switch},
                                  conf_root="configurations/",
                                  synthesis_name="VPLSSynthesis",
                                  synthesis_params=None)

        nc.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

        nc_list.append(nc)

    return nc_list


def main():

    num_iterations = 1
    num_grids_list = [1, 2, 3, 4]

    nc_list = prepare_network_configurations(num_grids_list)


    exp = SecurityPolicyTimes(nc_list, num_iterations)
    exp.trigger()
    exp.dump_data()

if __name__ == "__main__":
    main()
