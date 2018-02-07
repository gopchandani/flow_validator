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
        cls.nc_ring_dij = NetworkConfiguration("ryu",
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

        cls.ng_ring_dij = cls.nc_ring_dij.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

        cls.fv_ring_dij = FlowValidator(cls.ng_ring_dij)
        cls.fv_ring_dij.init_network_port_graph()

        cls.nc_clique_dij = NetworkConfiguration("ryu",
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

        cls.ng_clique_dij = cls.nc_clique_dij.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

        cls.fv_clique_dij = FlowValidator(cls.ng_clique_dij)
        cls.fv_clique_dij.init_network_port_graph()

        cls.nc_clique_arb = NetworkConfiguration("ryu",
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

        cls.ng_clique_arb = cls.nc_clique_arb.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

        cls.fv_clique_arb = FlowValidator(cls.ng_clique_arb)
        cls.fv_clique_arb.init_network_port_graph()

        cls.nc_ring_arb = NetworkConfiguration("ryu",
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
                                               synthesis_name="AboresceneSynthesis",
                                               synthesis_params={"apply_group_intents_immediately": True})

        cls.ng_ring_arb = cls.nc_ring_arb.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

        cls.fv_ring_arb = FlowValidator(cls.ng_ring_arb)
        cls.fv_ring_arb.init_network_port_graph()

    def test_connectivity_clique_dij_with_single_switch_failure(self):

        # Fail all links to one switch at a time and check if there are six violations for flows to/from the failed sw
        for sw_obj in self.ng_clique_dij.get_switches():

            sw_host_port = sw_obj.attached_hosts[0].switch_port
            src_zone = [sw_host_port]

            dst_zone = []
            for h_id in self.fv_clique_dij.network_graph.host_ids:
                if h_id != sw_obj.attached_hosts[0].node_id:
                    dst_zone.append(self.fv_clique_dij.network_graph.get_node_object(h_id).switch_port)

            specific_traffic = Traffic(init_wildcard=True)
            specific_traffic.set_field("ethernet_type", 0x0800)
            constraints = [PolicyConstraint(CONNECTIVITY_CONSTRAINT, None)]

            lmbdas = tuple(self.ng_clique_dij.get_switch_link_data(sw=sw_obj))

            # Outgoing flows
            s_o = PolicyStatement(self.ng_clique_dij,
                                  src_zone,
                                  dst_zone,
                                  specific_traffic,
                                  constraints,
                                  lmbdas=[lmbdas])

            s_i = PolicyStatement(self.ng_clique_dij,
                                  dst_zone,
                                  src_zone,
                                  specific_traffic,
                                  constraints,
                                  lmbdas=[lmbdas])

            violations = self.fv_clique_dij.validate_policy([s_o, s_i], optimization_type="With Preemption")

            self.assertEqual(len(violations), 6)

    def test_connectivity_ring_dij_with_single_link_failure(self):

        # Fail one link at a time and check that no flows are affected.

        for lmbda in itertools.permutations(self.ng_ring_dij.L, 1):

            src_zone = [self.fv_ring_dij.network_graph.get_node_object(h_id).switch_port
                        for h_id in self.fv_ring_dij.network_graph.host_ids]
            dst_zone = [self.fv_ring_dij.network_graph.get_node_object(h_id).switch_port
                        for h_id in self.fv_ring_dij.network_graph.host_ids]

            specific_traffic = Traffic(init_wildcard=True)
            specific_traffic.set_field("ethernet_type", 0x0800)
            constraints = [PolicyConstraint(CONNECTIVITY_CONSTRAINT, None)]

            # Outgoing flows
            s_o = PolicyStatement(self.ng_ring_dij,
                                  src_zone,
                                  dst_zone,
                                  specific_traffic,
                                  constraints,
                                  lmbdas=[lmbda])

            s_i = PolicyStatement(self.ng_ring_dij,
                                  dst_zone,
                                  src_zone,
                                  specific_traffic,
                                  constraints,
                                  lmbdas=[lmbda])

            violations = self.fv_ring_dij.validate_policy([s_o, s_i], optimization_type="With Preemption")

            self.assertEqual(len(violations), 0)

    def test_connectivity_clique_arb_with_single_switch_failure(self):

        # Fail all links to one switch at a time and check if there are six violations for flows to/from the failed sw
        for sw_obj in self.ng_clique_arb.get_switches():

            sw_host_port = sw_obj.attached_hosts[0].switch_port
            src_zone = [sw_host_port]

            dst_zone = []
            for h_id in self.fv_clique_arb.network_graph.host_ids:
                if h_id != sw_obj.attached_hosts[0].node_id:
                    dst_zone.append(self.fv_clique_arb.network_graph.get_node_object(h_id).switch_port)

            specific_traffic = Traffic(init_wildcard=True)
            specific_traffic.set_field("ethernet_type", 0x0800)
            constraints = [PolicyConstraint(CONNECTIVITY_CONSTRAINT, None)]

            lmbdas = tuple(self.ng_clique_arb.get_switch_link_data(sw=sw_obj))

            # Outgoing flows
            s_o = PolicyStatement(self.ng_clique_arb,
                                  src_zone,
                                  dst_zone,
                                  specific_traffic,
                                  constraints,
                                  lmbdas=[lmbdas])

            s_i = PolicyStatement(self.ng_clique_arb,
                                  dst_zone,
                                  src_zone,
                                  specific_traffic,
                                  constraints,
                                  lmbdas=[lmbdas])

            violations = self.fv_clique_arb.validate_policy([s_o, s_i], optimization_type="With Preemption")

            self.assertEqual(len(violations), 6)

    def test_connectivity_ring_arb_with_single_link_failure(self):

        # Fail one link at a time and check that no flows are affected.

        for lmbda in itertools.permutations(self.ng_ring_arb.L, 1):

            src_zone = [self.fv_ring_arb.network_graph.get_node_object(h_id).switch_port
                        for h_id in ['h11']]#self.fv_ring_arb.network_graph.host_ids]
            dst_zone = [self.fv_ring_arb.network_graph.get_node_object(h_id).switch_port
                        for h_id in ['h21']]#self.fv_ring_arb.network_graph.host_ids]

            specific_traffic = Traffic(init_wildcard=True)
            specific_traffic.set_field("ethernet_type", 0x0800)
            constraints = [PolicyConstraint(CONNECTIVITY_CONSTRAINT, None)]

            # Outgoing flows
            s_o = PolicyStatement(self.ng_ring_arb,
                                  src_zone,
                                  dst_zone,
                                  specific_traffic,
                                  constraints,
                                  lmbdas=[lmbda])

            # s_i = PolicyStatement(self.ng_ring_arb,
            #                       dst_zone,
            #                       src_zone,
            #                       specific_traffic,
            #                       constraints,
            #                       lmbdas=[lmbda])

            #violations = self.fv_ring_arb.validate_policy([s_o, s_i], optimization_type="With Preemption")
            violations = self.fv_ring_arb.validate_policy([s_o], optimization_type="With Preemption")

            self.assertEqual(len(violations), 0)


if __name__ == '__main__':
    unittest.main()

