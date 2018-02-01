import unittest
from model.traffic import Traffic
from experiments.network_configuration import NetworkConfiguration
from analysis.flow_validator import FlowValidator
from analysis.policy_statement import PolicyStatement, PolicyConstraint
from analysis.policy_statement import CONNECTIVITY_CONSTRAINT, PATH_LENGTH_CONSTRAINT, LINK_AVOIDANCE_CONSTRAINT


class TestFlowValidator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.nc = NetworkConfiguration("ryu",
                                      "127.0.0.1",
                                      6633,
                                      "http://localhost:8080/",
                                      "admin",
                                      "admin",
                                      "cliquetopo",
                                      {"num_switches": 4,
                                       "num_hosts_per_switch": 1,
                                       "per_switch_links": 2},
                                      conf_root="configurations/",
                                      synthesis_name="DijkstraSynthesis",
                                      synthesis_params={"apply_group_intents_immediately": True})

        cls.ng = cls.nc.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

        cls.fv = FlowValidator(cls.ng)
        cls.fv.init_network_port_graph()

    def test_connectivity_with_single_switch_failure(self):
        # On a 4-clique topology with one switch per host, every one of the four hosts is connected to the others
        # killing out all the links to one switch and testing to see
        # if the FlowValidator detects all the violations

        for sw_obj in self.ng.get_switches():

            sw_host_port = sw_obj.attached_hosts[0].switch_port
            src_zone = [sw_host_port]

            dst_zone = []
            for h_id in self.fv.network_graph.host_ids:
                if h_id != sw_obj.attached_hosts[0].node_id:
                    dst_zone.append(self.fv.network_graph.get_node_object(h_id).switch_port)

            specific_traffic = Traffic(init_wildcard=True)
            specific_traffic.set_field("ethernet_type", 0x0800)
            constraints = [PolicyConstraint(CONNECTIVITY_CONSTRAINT, None)]

            lmbdas = tuple(self.ng.get_switch_link_data(sw=sw_obj))

            # Outgoing flows
            s_o = PolicyStatement(self.nc.ng,
                                  src_zone,
                                  dst_zone,
                                  specific_traffic,
                                  constraints,
                                  lmbdas=[lmbdas])

            s_i = PolicyStatement(self.nc.ng,
                                  dst_zone,
                                  src_zone,
                                  specific_traffic,
                                  constraints,
                                  lmbdas=[lmbdas])

            violations = self.fv.validate_policy([s_o, s_i], optimization_type="With Preemption")

            # There are six flows in each case
            self.assertEqual(len(violations), 6)


if __name__ == '__main__':
    unittest.main()

