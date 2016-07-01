import unittest
import os
from model.switch_port_graph import SwitchPortGraph
from model.traffic import Traffic
from model.intervaltree_modified import Interval

from experiments.network_configuration import NetworkConfiguration


class TestSwitchPortGraph(unittest.TestCase):

    def setUp(self):

        nc = NetworkConfiguration("ryu",
                                  "ring",
                                  {"num_switches": 4,
                                   "num_hosts_per_switch": 1},
                                  conf_root=os.path.dirname(__file__) + "/",
                                  synthesis_name="AboresceneSynthesis",
                                  synthesis_params={"apply_group_intents_immediately": True})

        self.ng = nc.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)
        sw = self.ng.get_node_object("s1")
        self.ring_swpg = SwitchPortGraph(self.ng, sw, True)
        sw.port_graph = self.ring_swpg
        self.ring_swpg.init_switch_port_graph()
        self.ring_swpg.compute_switch_admitted_traffic()

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

        return at_int

    def check_vlan_tag_push_and_modification(self, at, modified_interval):
        vlan_tag_modification = at.traffic_elements[0].switch_modifications["vlan_id"][1]
        self.assertEqual(modified_interval, vlan_tag_modification)

    def test_ring_aborescene_synthesis_admitted_traffic(self):

        # This test asserts that in switch s1, for host h11, with no failures:
        # Traffic for host h21 flows out of port 3
        # Traffic for host h31 flows out of port 2
        # Traffic for host h41 flows out of port 2

        h11_obj = self.ng.get_node_object("h11")
        h21_obj = self.ng.get_node_object("h21")
        h31_obj = self.ng.get_node_object("h31")
        h41_obj = self.ng.get_node_object("h41")

        at_int = self.check_admitted_traffic(self.ring_swpg, h11_obj, h21_obj, 1, 3)
        at_int = self.check_admitted_traffic(self.ring_swpg, h11_obj, h31_obj, 1, 2)
        at_int = self.check_admitted_traffic(self.ring_swpg, h11_obj, h41_obj, 1, 2)

    def test_ring_aborescene_synthesis_modifications(self):

        # This test asserts that in switch s1, for host h11, with no failures:
        # Traffic for host h21 flows out of port 3 with modifications 5122
        # Traffic for host h31 flows out of port 2 with modifications 5123
        # Traffic for host h41 flows out of port 2 with modifications 5124

        h11_obj = self.ng.get_node_object("h11")
        h21_obj = self.ng.get_node_object("h21")
        h31_obj = self.ng.get_node_object("h31")
        h41_obj = self.ng.get_node_object("h41")

        at_int = self.check_admitted_traffic(self.ring_swpg, h11_obj, h21_obj, 1, 3)
        self.check_vlan_tag_push_and_modification(at_int, Interval(5122, 5123))

        at_int = self.check_admitted_traffic(self.ring_swpg, h11_obj, h31_obj, 1, 2)
        self.check_vlan_tag_push_and_modification(at_int, Interval(5123, 5124))

        at_int = self.check_admitted_traffic(self.ring_swpg, h11_obj, h41_obj, 1, 2)
        self.check_vlan_tag_push_and_modification(at_int, Interval(5124, 5125))

    # def test_single_port_failure(self, verbose=False):
    #
    #     # This test asserts that in switch s1, for host h11, with a single failures:
    #     # Traffic for host h21 flows out of port 3 with modifications 5122 before failure and
    #     # out of port 2 with modifications 6146 after failure
    #     # Traffic for host h31 flows out of port 3 with modifications 5123 before failure and
    #     # out of port 2 with modifications 6147 after failure
    #     # Traffic for host h41 flows out of port 3 with modifications 5124 before failure and
    #     # out of port 2 with modifications 6148 after failure
    #
    #     h11_obj = self.ng.get_node_object("h11")
    #     h21_obj = self.ng.get_node_object("h21")
    #     h31_obj = self.ng.get_node_object("h31")
    #     h41_obj = self.ng.get_node_object("h41")
    #
    #     specific_traffic = Traffic(init_wildcard=True)
    #     specific_traffic.set_field("ethernet_type", 0x0800)
    #     specific_traffic.set_field("ethernet_source", int(h11_obj.mac_addr.replace(":", ""), 16))
    #     specific_traffic.set_field("in_port", int(h11_obj.switch_port_attached))
    #     specific_traffic.set_field("vlan_id", h11_obj.switch_obj.synthesis_tag + 0x1000, is_exception_value=True)
    #     specific_traffic.set_field("has_vlan_tag", 0)
    #
    #     ingress_node_1 = self.ring_swpg.get_ingress_node("s1", 1)
    #     egress_node_2 = self.ring_swpg.get_egress_node("s1", 2)
    #     egress_node_3 = self.ring_swpg.get_egress_node("s1", 3)
    #
    #     specific_traffic.set_field("ethernet_destination", int(h21_obj.mac_addr.replace(":", ""), 16))
    #     before_at = self.ring_swpg.get_admitted_traffic(ingress_node_1, egress_node_3)
    #     before_at_int = specific_traffic.intersect(before_at)
    #     before_vlan_tag_modification = before_at_int.traffic_elements[0].switch_modifications["vlan_id"][1]
    #
    #     testing_port_number = 3
    #     testing_port = self.ring_swpg.sw.ports[testing_port_number]
    #     testing_port.state = "down"
    #     end_to_end_modified_edges = self.ring_swpg.update_admitted_traffic_due_to_port_state_change(testing_port_number,
    #                                                                                            "port_down")
    #     after_at = self.ring_swpg.get_admitted_traffic(ingress_node_1, egress_node_2)
    #     after_at_int = specific_traffic.intersect(after_at)
    #     after_vlan_tag_modification = after_at_int.traffic_elements[0].switch_modifications["vlan_id"][1]
    #
    #     is_traffic_equal = before_at_int.is_equal_traffic(after_at_int)
    #
    #     self.assertEqual(is_traffic_equal, True)
    #     self.assertEqual(before_vlan_tag_modification, Interval(5122, 5123))
    #     self.assertEqual(after_vlan_tag_modification, Interval(6146, 6147))
    #
    #     testing_port.state = "up"
    #     end_to_end_modified_edges = self.ring_swpg.update_admitted_traffic_due_to_port_state_change(testing_port_number,
    #                                                                                            "port_up")
    #
    #     specific_traffic.set_field("ethernet_destination", int(h31_obj.mac_addr.replace(":", ""), 16))
    #     before_at = self.ring_swpg.get_admitted_traffic(ingress_node_1, egress_node_2)
    #     before_at_int = specific_traffic.intersect(before_at)
    #     before_vlan_tag_modification = before_at_int.traffic_elements[0].switch_modifications["vlan_id"][1]
    #
    #     testing_port_number = 2
    #     testing_port = self.ring_swpg.sw.ports[testing_port_number]
    #     testing_port.state = "down"
    #     end_to_end_modified_edges = self.ring_swpg.update_admitted_traffic_due_to_port_state_change(testing_port_number,
    #                                                                                            "port_down")
    #     after_at = self.ring_swpg.get_admitted_traffic(ingress_node_1, egress_node_3)
    #     after_at_int = specific_traffic.intersect(after_at)
    #     after_vlan_tag_modification = after_at_int.traffic_elements[0].switch_modifications["vlan_id"][1]
    #
    #     is_traffic_equal = before_at_int.is_equal_traffic(after_at_int)
    #
    #     self.assertEqual(is_traffic_equal, True)
    #     self.assertEqual(before_vlan_tag_modification, Interval(5123, 5124))
    #     self.assertEqual(after_vlan_tag_modification, Interval(6147, 6148))
    #
    #     testing_port.state = "up"
    #     end_to_end_modified_edges = self.ring_swpg.update_admitted_traffic_due_to_port_state_change(testing_port_number,
    #                                                                                            "port_up")
    #
    #     specific_traffic.set_field("ethernet_destination", int(h41_obj.mac_addr.replace(":", ""), 16))
    #     before_at = self.ring_swpg.get_admitted_traffic(ingress_node_1, egress_node_2)
    #     before_at_int = specific_traffic.intersect(before_at)
    #     before_vlan_tag_modification = before_at_int.traffic_elements[0].switch_modifications["vlan_id"][1]
    #
    #     testing_port_number = 2
    #     testing_port = self.ring_swpg.sw.ports[testing_port_number]
    #     testing_port.state = "down"
    #     end_to_end_modified_edges = self.ring_swpg.update_admitted_traffic_due_to_port_state_change(testing_port_number,
    #                                                                                            "port_down")
    #     after_at = self.ring_swpg.get_admitted_traffic(ingress_node_1, egress_node_3)
    #     after_at_int = specific_traffic.intersect(after_at)
    #     after_vlan_tag_modification = after_at_int.traffic_elements[0].switch_modifications["vlan_id"][1]
    #
    #     is_traffic_equal = before_at_int.is_equal_traffic(after_at_int)
    #
    #     self.assertEqual(is_traffic_equal, True)
    #     self.assertEqual(before_vlan_tag_modification, Interval(5124, 5125))
    #     self.assertEqual(after_vlan_tag_modification, Interval(6148, 6149))
    #
    #     testing_port.state = "up"
    #     end_to_end_modified_edges = self.ring_swpg.update_admitted_traffic_due_to_port_state_change(testing_port_number,
    #                                                                                            "port_up")
    #
    # def test_all_ports_failure_restore(self, verbose=False):
    #
    #     test_passed = True
    #
    #     # Loop over ports of the switch and fail and restore them one by one
    #     for testing_port_number in self.ring_swpg.sw.ports:
    #
    #         print "testing_port_number:", testing_port_number
    #
    #         testing_port = self.ring_swpg.sw.ports[testing_port_number]
    #
    #         graph_paths_before = self.ring_swpg.get_graph_paths(verbose)
    #         graph_ats_before = self.ring_swpg.get_graph_at()
    #
    #         testing_port.state = "down"
    #         end_to_end_modified_edges = self.ring_swpg.update_admitted_traffic_due_to_port_state_change(testing_port_number,
    #                                                                                                "port_down")
    #
    #         graph_paths_intermediate = self.ring_swpg.get_graph_paths(verbose)
    #         graph_ats_intermediate = self.ring_swpg.get_graph_at()
    #
    #         testing_port.state = "up"
    #         end_to_end_modified_edges = self.ring_swpg.update_admitted_traffic_due_to_port_state_change(testing_port_number,
    #                                                                                                "port_up")
    #
    #         graph_paths_after = self.ring_swpg.get_graph_paths(verbose)
    #         graph_ats_after = self.ring_swpg.get_graph_at()
    #
    #         all_graph_paths_equal = self.ring_swpg.compare_graph_paths(graph_paths_before,
    #                                                               graph_paths_after,
    #                                                               verbose)
    #
    #         if not all_graph_paths_equal:
    #             test_passed = all_graph_paths_equal
    #             print "Test Failed."
    #
    #         all_graph_ats_equal = self.ring_swpg.compare_graph_ats(graph_ats_before,
    #                                                           graph_ats_after,
    #                                                           verbose)
    #         if not all_graph_ats_equal:
    #             test_passed = all_graph_ats_equal
    #             print "Test Failed."
    #
    #     self.assertEqual(test_passed, True)

if __name__ == '__main__':
    unittest.main()
