import unittest
import os
from model.switch_port_graph import SwitchPortGraph
from model.traffic import Traffic
from model.traffic_path import TrafficPath
from model.intervaltree_modified import Interval

from experiments.network_configuration import NetworkConfiguration


class TestSwitchPortGraph(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        nc = NetworkConfiguration("ryu",
                                  "ring",
                                  {"num_switches": 4,
                                   "num_hosts_per_switch": 1},
                                  conf_root=os.path.dirname(__file__) + "/",
                                  synthesis_name="AboresceneSynthesis",
                                  synthesis_params={"apply_group_intents_immediately": True})

        cls.ng = nc.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)
        sw = cls.ng.get_node_object("s1")
        cls.ring_swpg = SwitchPortGraph(cls.ng, sw, True)
        sw.port_graph = cls.ring_swpg
        cls.ring_swpg.init_switch_port_graph()
        cls.ring_swpg.compute_switch_admitted_traffic()

    def check_admitted_traffic(self, swpg, src_host_obj, dst_host_obj, ingress_port_num, egress_port_num):
        ingress_node = swpg.get_ingress_node(swpg.sw.node_id, ingress_port_num)
        egress_node = swpg.get_egress_node(swpg.sw.node_id, egress_port_num)

        specific_traffic = Traffic(init_wildcard=True)
        specific_traffic.set_field("ethernet_type", 0x0800)
        specific_traffic.set_field("ethernet_source", int(src_host_obj.mac_addr.replace(":", ""), 16))
        specific_traffic.set_field("ethernet_destination", int(dst_host_obj.mac_addr.replace(":", ""), 16))
        specific_traffic.set_field("in_port", int(src_host_obj.switch_port_attached))
        specific_traffic.set_field("vlan_id", src_host_obj.switch_obj.synthesis_tag + 0x1000, is_exception_value=True)
        specific_traffic.set_field("has_vlan_tag", 0)

        at_int = specific_traffic.intersect(swpg.get_admitted_traffic(ingress_node, egress_node))
        self.assertNotEqual(at_int.is_empty(), True)

        return at_int, ingress_node, egress_node

    def check_failover_admitted_traffic(self, swpg, src_host_obj, dst_host_obj,
                                        ingress_port_num,
                                        primary_egress_port_num,
                                        failover_egress_port_num):

        primary_at_int, ingress_node, egress_node = self.check_admitted_traffic(swpg, src_host_obj,
                                                                                dst_host_obj,
                                                                                ingress_port_num,
                                                                                primary_egress_port_num)

        testing_port = swpg.sw.ports[primary_egress_port_num]
        testing_port.state = "down"
        swpg.update_admitted_traffic_due_to_port_state_change(primary_egress_port_num, "port_down")

        failover_at_int, ingress_node, egress_node = self.check_admitted_traffic(swpg, src_host_obj,
                                                                                 dst_host_obj,
                                                                                 ingress_port_num,
                                                                                 failover_egress_port_num)

        testing_port.state = "up"
        swpg.update_admitted_traffic_due_to_port_state_change(primary_egress_port_num, "port_up")

        return primary_at_int, failover_at_int

    def check_modifications(self, at, expected_modified_fields):

        for mf in expected_modified_fields:
            vlan_tag_modification = at.traffic_elements[0].switch_modifications[mf][1]
            self.assertEqual(expected_modified_fields[mf], vlan_tag_modification)

    def check_failover_modifications(self, primary_at, failover_at,
                                     primary_expected_modified_fields, failover_expected_modified_fields):

        self.check_modifications(primary_at, primary_expected_modified_fields)
        self.check_modifications(failover_at, failover_expected_modified_fields)

    def check_path(self, swpg, at, ingress_node, egress_node, expected_path):

        all_paths = swpg.get_paths(ingress_node,
                                   egress_node,
                                   at,
                                   [ingress_node],
                                   [],
                                   False)

        self.assertEqual(len(all_paths), 1)
        self.assertEqual(all_paths[0], expected_path)

    def check_failover_path(self, swpg, src_host_obj, dst_host_obj,
                            ingress_port_num, primary_egress_port_num, failover_egress_port_num,
                            primary_expected_path, failover_expected_path):

        primary_at_int, ingress_node, egress_node = self.check_admitted_traffic(swpg, src_host_obj,
                                                                                dst_host_obj,
                                                                                ingress_port_num,
                                                                                primary_egress_port_num)

        self.check_path(swpg, primary_at_int, ingress_node, egress_node, primary_expected_path)

        testing_port = swpg.sw.ports[primary_egress_port_num]
        testing_port.state = "down"
        swpg.update_admitted_traffic_due_to_port_state_change(primary_egress_port_num, "port_down")

        failover_at_int, ingress_node, egress_node = self.check_admitted_traffic(swpg, src_host_obj,
                                                                                 dst_host_obj,
                                                                                 ingress_port_num,
                                                                                 failover_egress_port_num)

        self.check_path(swpg, primary_at_int, ingress_node, egress_node, failover_expected_path)

        testing_port.state = "up"
        swpg.update_admitted_traffic_due_to_port_state_change(primary_egress_port_num, "port_up")

        return primary_at_int, failover_at_int

    def test_ring_aborescene_synthesis_admitted_traffic(self):

        # This test asserts that in switch s1, for host h11, with no failures:
        # Traffic for host h21 flows out of port 3
        # Traffic for host h31 flows out of port 2
        # Traffic for host h41 flows out of port 2

        h11_obj = self.ng.get_node_object("h11")
        h21_obj = self.ng.get_node_object("h21")
        h31_obj = self.ng.get_node_object("h31")
        h41_obj = self.ng.get_node_object("h41")

        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.ring_swpg, h11_obj, h21_obj, 1, 3)
        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.ring_swpg, h11_obj, h31_obj, 1, 2)
        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.ring_swpg, h11_obj, h41_obj, 1, 2)

    def test_ring_aborescene_synthesis_modifications(self):

        # This test asserts that in switch s1, for host h11, with no failures:
        # Traffic for host h21 flows out of port 3 with modifications 5122
        # Traffic for host h31 flows out of port 2 with modifications 5123
        # Traffic for host h41 flows out of port 2 with modifications 5124

        h11_obj = self.ng.get_node_object("h11")
        h21_obj = self.ng.get_node_object("h21")
        h31_obj = self.ng.get_node_object("h31")
        h41_obj = self.ng.get_node_object("h41")

        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.ring_swpg, h11_obj, h21_obj, 1, 3)
        self.check_modifications(at_int, {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(5122, 5123)})

        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.ring_swpg, h11_obj, h31_obj, 1, 2)
        self.check_modifications(at_int, {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(5123, 5124)})

        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.ring_swpg, h11_obj, h41_obj, 1, 2)
        self.check_modifications(at_int, {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(5124, 5125)})

    def test_ring_aborescene_synthesis_paths(self):

        # This test asserts that in switch s1, for host h11, with no failures:
        # Traffic for host h21 flows out of port 3 via the specified path below
        # Traffic for host h31 flows out of port 2 via the specified path below
        # Traffic for host h41 flows out of port 2 via the specified path below

        h11_obj = self.ng.get_node_object("h11")
        h21_obj = self.ng.get_node_object("h21")
        h31_obj = self.ng.get_node_object("h31")
        h41_obj = self.ng.get_node_object("h41")

        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.ring_swpg, h11_obj, h21_obj, 1, 3)
        expected_path = TrafficPath(self.ring_swpg, [self.ring_swpg.get_node("s1:ingress1"),
                                                     self.ring_swpg.get_node("s1:table0"),
                                                     self.ring_swpg.get_node("s1:table1"),
                                                     self.ring_swpg.get_node("s1:table2"),
                                                     self.ring_swpg.get_node("s1:table3"),
                                                     self.ring_swpg.get_node("s1:egress3")])
        self.check_path(self.ring_swpg, at_int, ingress_node, egress_node, expected_path)

        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.ring_swpg, h11_obj, h31_obj, 1, 2)
        expected_path = TrafficPath(self.ring_swpg, [self.ring_swpg.get_node("s1:ingress1"),
                                                     self.ring_swpg.get_node("s1:table0"),
                                                     self.ring_swpg.get_node("s1:table1"),
                                                     self.ring_swpg.get_node("s1:table2"),
                                                     self.ring_swpg.get_node("s1:table3"),
                                                     self.ring_swpg.get_node("s1:egress2")])
        self.check_path(self.ring_swpg, at_int, ingress_node, egress_node, expected_path)

        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.ring_swpg, h11_obj, h41_obj, 1, 2)
        expected_path = TrafficPath(self.ring_swpg, [self.ring_swpg.get_node("s1:ingress1"),
                                                     self.ring_swpg.get_node("s1:table0"),
                                                     self.ring_swpg.get_node("s1:table1"),
                                                     self.ring_swpg.get_node("s1:table2"),
                                                     self.ring_swpg.get_node("s1:table3"),
                                                     self.ring_swpg.get_node("s1:egress2")])
        self.check_path(self.ring_swpg, at_int, ingress_node, egress_node, expected_path)

    def test_ring_aborescene_synthesis_admitted_traffic_failover(self):

        # This test asserts that in switch s1, for host h11, with a single failures:
        # Traffic for host h21 flows out of port 3 before failure and out of port 2 after failure
        # Traffic for host h31 flows out of port 2 before failure and out of port 3 after failure
        # Traffic for host h41 flows out of port 2 before failure and out of port 3 after failure

        h11_obj = self.ng.get_node_object("h11")
        h21_obj = self.ng.get_node_object("h21")
        h31_obj = self.ng.get_node_object("h31")
        h41_obj = self.ng.get_node_object("h41")

        self.check_failover_admitted_traffic(self.ring_swpg, h11_obj, h21_obj, 1, 3, 2)
        self.check_failover_admitted_traffic(self.ring_swpg, h11_obj, h31_obj, 1, 2, 3)
        self.check_failover_admitted_traffic(self.ring_swpg, h11_obj, h41_obj, 1, 2, 3)

    def test_ring_aborescene_synthesis_modifications_failover(self):

        # This test asserts that in switch s1, for host h11, with a single failures:
        # Traffic for host h21 flows out of port 3 with modifications 5122 before failure and
        # out of port 2 with modifications 6146 after failure
        # Traffic for host h31 flows out of port 2 with modifications 5123 before failure and
        # out of port 3 with modifications 6147 after failure
        # Traffic for host h41 flows out of port 2 with modifications 5124 before failure and
        # out of port 3 with modifications 6148 after failure

        h11_obj = self.ng.get_node_object("h11")
        h21_obj = self.ng.get_node_object("h21")
        h31_obj = self.ng.get_node_object("h31")
        h41_obj = self.ng.get_node_object("h41")

        primary_at, failover_at = self.check_failover_admitted_traffic(self.ring_swpg, h11_obj, h21_obj, 1, 3, 2)
        self.check_failover_modifications(primary_at, failover_at,
                                          {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(5122, 5123)},
                                          {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(6146, 6147)})

        primary_at, failover_at = self.check_failover_admitted_traffic(self.ring_swpg, h11_obj, h31_obj, 1, 2, 3)
        self.check_failover_modifications(primary_at, failover_at,
                                          {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(5123, 5124)},
                                          {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(6147, 6148)})

        primary_at, failover_at = self.check_failover_admitted_traffic(self.ring_swpg, h11_obj, h41_obj, 1, 2, 3)
        self.check_failover_modifications(primary_at, failover_at,
                                          {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(5124, 5125)},
                                          {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(6148, 6149)})

    def test_ring_aborescene_synthesis_paths_failover(self):

        # This test asserts that in switch s1, for host h11, with a single failures:
        # Traffic for host h21 flows out of port 3 before failure and out of port 2 after failure
        # Traffic for host h31 flows out of port 2 before failure and out of port 3 after failure
        # Traffic for host h41 flows out of port 2 before failure and out of port 3 after failure

        h11_obj = self.ng.get_node_object("h11")
        h21_obj = self.ng.get_node_object("h21")
        h31_obj = self.ng.get_node_object("h31")
        h41_obj = self.ng.get_node_object("h41")

        expected_path_via_egress2 = TrafficPath(self.ring_swpg, [self.ring_swpg.get_node("s1:ingress1"),
                                                     self.ring_swpg.get_node("s1:table0"),
                                                     self.ring_swpg.get_node("s1:table1"),
                                                     self.ring_swpg.get_node("s1:table2"),
                                                     self.ring_swpg.get_node("s1:table3"),
                                                     self.ring_swpg.get_node("s1:egress2")])

        expected_path_via_egress3 = TrafficPath(self.ring_swpg, [self.ring_swpg.get_node("s1:ingress1"),
                                                     self.ring_swpg.get_node("s1:table0"),
                                                     self.ring_swpg.get_node("s1:table1"),
                                                     self.ring_swpg.get_node("s1:table2"),
                                                     self.ring_swpg.get_node("s1:table3"),
                                                     self.ring_swpg.get_node("s1:egress3")])

        self.check_failover_path(self.ring_swpg, h11_obj, h21_obj, 1, 3, 2,
                                 expected_path_via_egress3, expected_path_via_egress2)

        self.check_failover_path(self.ring_swpg, h11_obj, h31_obj, 1, 2, 3,
                                 expected_path_via_egress2, expected_path_via_egress3)

        self.check_failover_path(self.ring_swpg, h11_obj, h41_obj, 1, 2, 3,
                                 expected_path_via_egress2, expected_path_via_egress3)

    def test_all_ports_failure_restore(self, verbose=False):

        test_passed = True

        # Loop over ports of the switch and fail and restore them one by one
        for testing_port_number in self.ring_swpg.sw.ports:

            testing_port = self.ring_swpg.sw.ports[testing_port_number]

            graph_paths_before = self.ring_swpg.get_graph_paths(verbose)
            graph_ats_before = self.ring_swpg.get_graph_at()

            testing_port.state = "down"
            end_to_end_modified_edges = self.ring_swpg.update_admitted_traffic_due_to_port_state_change(testing_port_number,
                                                                                                        "port_down")

            graph_paths_intermediate = self.ring_swpg.get_graph_paths(verbose)
            graph_ats_intermediate = self.ring_swpg.get_graph_at()

            testing_port.state = "up"
            end_to_end_modified_edges = self.ring_swpg.update_admitted_traffic_due_to_port_state_change(testing_port_number,
                                                                                                        "port_up")

            graph_paths_after = self.ring_swpg.get_graph_paths(verbose)
            graph_ats_after = self.ring_swpg.get_graph_at()

            all_graph_paths_equal = self.ring_swpg.compare_graph_paths(graph_paths_before,
                                                                       graph_paths_after,
                                                                       verbose)

            if not all_graph_paths_equal:
                test_passed = all_graph_paths_equal

            all_graph_ats_equal = self.ring_swpg.compare_graph_ats(graph_ats_before,
                                                                   graph_ats_after,
                                                                   verbose)
            if not all_graph_ats_equal:
                test_passed = all_graph_ats_equal

        self.assertEqual(test_passed, True)

if __name__ == '__main__':
    unittest.main()
