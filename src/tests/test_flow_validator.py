import unittest
import itertools
from model.traffic import Traffic
from model.network_configuration import NetworkConfiguration
from analysis.flow_validator import FlowValidator
from analysis.policy_statement import PolicyStatement, PolicyConstraint
from analysis.policy_statement import CONNECTIVITY_CONSTRAINT


class TestFlowValidator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.nc_ring = NetworkConfiguration("ryu",
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

        cls.ng_ring = cls.nc_ring.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

        cls.fv_ring = FlowValidator(cls.ng_ring)
        cls.fv_ring.init_network_port_graph()

        cls.nc_clique = NetworkConfiguration("ryu",
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
                                             synthesis_name="DijkstraSynthesis",
                                             synthesis_params={"apply_group_intents_immediately": True})

        cls.ng_clique = cls.nc_clique.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

        cls.fv_clique = FlowValidator(cls.ng_clique)
        cls.fv_clique.init_network_port_graph()

    def test_connectivity_clique_with_single_switch_failure(self):

        # Fail all links to one switch at a time and check if there are six violations for flows to/from the failed sw
        for sw_obj in self.ng_clique.get_switches():

            sw_host_port = sw_obj.attached_hosts[0].switch_port
            src_zone = [sw_host_port]

            dst_zone = []
            for h_id in self.fv_clique.network_graph.host_ids:
                if h_id != sw_obj.attached_hosts[0].node_id:
                    dst_zone.append(self.fv_clique.network_graph.get_node_object(h_id).switch_port)

            specific_traffic = Traffic(init_wildcard=True)
            specific_traffic.set_field("ethernet_type", 0x0800)
            constraints = [PolicyConstraint(CONNECTIVITY_CONSTRAINT, None)]

            lmbdas = tuple(self.ng_clique.get_switch_link_data(sw=sw_obj))

            # Outgoing flows
            s_o = PolicyStatement(self.nc_clique.ng,
                                  src_zone,
                                  dst_zone,
                                  specific_traffic,
                                  constraints,
                                  lmbdas=[lmbdas])

            s_i = PolicyStatement(self.nc_clique.ng,
                                  dst_zone,
                                  src_zone,
                                  specific_traffic,
                                  constraints,
                                  lmbdas=[lmbdas])

            violations = self.fv_clique.validate_policy([s_o, s_i], optimization_type="With Preemption")

            # There are six flows in each case
            self.assertEqual(len(violations), 6)

    def test_connectivity_ring_with_single_link_failure(self):

        # Fail one link at a time and check that no flows are affected.

        for lmbda in itertools.permutations(self.nc_ring.ng.L, 1):

            src_zone = [self.fv_ring.network_graph.get_node_object(h_id).switch_port
                        for h_id in self.fv_ring.network_graph.host_ids]
            dst_zone = [self.fv_ring.network_graph.get_node_object(h_id).switch_port
                        for h_id in self.fv_ring.network_graph.host_ids]

            specific_traffic = Traffic(init_wildcard=True)
            specific_traffic.set_field("ethernet_type", 0x0800)
            constraints = [PolicyConstraint(CONNECTIVITY_CONSTRAINT, None)]

            # Outgoing flows
            s_o = PolicyStatement(self.nc_ring.ng,
                                  src_zone,
                                  dst_zone,
                                  specific_traffic,
                                  constraints,
                                  lmbdas=[lmbda])

            s_i = PolicyStatement(self.nc_ring.ng,
                                  dst_zone,
                                  src_zone,
                                  specific_traffic,
                                  constraints,
                                  lmbdas=[lmbda])

            violations = self.fv_ring.validate_policy([s_o, s_i], optimization_type="With Preemption")

            # There are six flows in each case
            self.assertEqual(len(violations), 0)


if __name__ == '__main__':
    unittest.main()

