import unittest
import itertools
from model.traffic import Traffic
from experiments.network_configuration import NetworkConfiguration
from experiments.security_policy_times import construct_security_policy_statements
from analysis.flow_validator import FlowValidator
from analysis.policy_statement import PolicyStatement, PolicyConstraint
from analysis.policy_statement import CONNECTIVITY_CONSTRAINT


class TestFlowValidator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        ip_str = "172.17.0.2"
        port_str = "8181"
        num_switches_per_grid = 3
        num_grids = 1
        num_hosts_per_switch = 3
        cls.nc_microgrid = NetworkConfiguration("onos",
                                                ip_str,
                                                int(port_str),
                                                "http://" + ip_str + ":" + port_str + "/onos/v1/",
                                                "karaf",
                                                "karaf",
                                                "microgrid_topo",
                                                {"num_switches": 1 + 1 * num_switches_per_grid,
                                                 "nGrids": num_grids,
                                                 "nSwitchesPerGrid": num_switches_per_grid,
                                                 "nHostsPerSwitch": num_hosts_per_switch},
                                                conf_root="configurations/",
                                                synthesis_name=None,
                                                synthesis_params=None)

        cls.ng_microgrid = cls.nc_microgrid.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)
        cls.fv = FlowValidator(cls.ng_microgrid)
        cls.fv.init_network_port_graph()

    def test_ng_microgrid(self):
        policy_statements = construct_security_policy_statements(self.nc_microgrid)
        violations = self.fv.validate_policy(policy_statements)
        self.assertEqual(len(violations), 0)


if __name__ == '__main__':
    unittest.main()

