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

        nc_linear_dijkstra = NetworkConfiguration("ryu",
                                                  "linear",
                                                  {"num_switches": 2,
                                                   "num_hosts_per_switch": 1},
                                                  conf_root="configurations/",
                                                  synthesis_name="DijkstraSynthesis",
                                                  synthesis_params={"apply_group_intents_immediately": True})

        cls.ng_linear_dijkstra = nc_linear_dijkstra.setup_network_graph(mininet_setup_gap=1,
                                                                        synthesis_setup_gap=1)
        sw_linear_dijkstra = cls.ng_linear_dijkstra.get_node_object("s1")
        cls.swpg_linear_dijkstra = SwitchPortGraph(cls.ng_linear_dijkstra,
                                                   sw_linear_dijkstra, True)

        sw_linear_dijkstra.port_graph = cls.swpg_linear_dijkstra
        cls.swpg_linear_dijkstra.init_switch_port_graph()
        cls.swpg_linear_dijkstra.compute_switch_admitted_traffic()

        nc_ring_aborescene_apply_true = NetworkConfiguration("ryu",
                                                             "ring",
                                                             {"num_switches": 4,
                                                              "num_hosts_per_switch": 1},
                                                             conf_root=os.path.dirname(__file__) + "/",
                                                             synthesis_name="AboresceneSynthesis",
                                                             synthesis_params={"apply_group_intents_immediately": True})

        cls.ng_ring_aborescene_apply_true = nc_ring_aborescene_apply_true.setup_network_graph(mininet_setup_gap=1,
                                                                                              synthesis_setup_gap=1)
        sw_ring_aborescene_apply_true = cls.ng_ring_aborescene_apply_true.get_node_object("s1")
        cls.swpg_ring_aborescene_apply_true = SwitchPortGraph(cls.ng_ring_aborescene_apply_true,
                                                              sw_ring_aborescene_apply_true, True)

        sw_ring_aborescene_apply_true.port_graph = cls.swpg_ring_aborescene_apply_true
        cls.swpg_ring_aborescene_apply_true.init_switch_port_graph()
        cls.swpg_ring_aborescene_apply_true.compute_switch_admitted_traffic()

        nc_ring_aborescene_apply_false = NetworkConfiguration("ryu",
                                                              "ring",
                                                              {"num_switches": 4,
                                                               "num_hosts_per_switch": 1},
                                                              conf_root=os.path.dirname(__file__) + "/",
                                                              synthesis_name="AboresceneSynthesis",
                                                              synthesis_params={"apply_group_intents_immediately": False})

        cls.ng_ring_aborescene_apply_false = nc_ring_aborescene_apply_false.setup_network_graph(mininet_setup_gap=1,
                                                                                                synthesis_setup_gap=1)
        sw_ring_aborescene_apply_false = cls.ng_ring_aborescene_apply_false.get_node_object("s1")
        cls.swpg_ring_aborescene_apply_false = SwitchPortGraph(cls.ng_ring_aborescene_apply_false,
                                                               sw_ring_aborescene_apply_false, True)

        sw_ring_aborescene_apply_false.port_graph = cls.swpg_ring_aborescene_apply_false
        cls.swpg_ring_aborescene_apply_false.init_switch_port_graph()
        cls.swpg_ring_aborescene_apply_false.compute_switch_admitted_traffic()

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

        at = swpg.get_admitted_traffic(ingress_node, egress_node)
        at_int = specific_traffic.intersect(at)
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

        test_port = swpg.sw.ports[primary_egress_port_num]
        test_port.state = "down"
        swpg.update_admitted_traffic_due_to_port_state_change(primary_egress_port_num, "port_down")

        failover_at_int, ingress_node, egress_node = self.check_admitted_traffic(swpg, src_host_obj,
                                                                                 dst_host_obj,
                                                                                 ingress_port_num,
                                                                                 failover_egress_port_num)

        test_port.state = "up"
        swpg.update_admitted_traffic_due_to_port_state_change(primary_egress_port_num, "port_up")

        return primary_at_int, failover_at_int

    def check_modifications(self, at, expected_modified_fields):

        for mf in expected_modified_fields:
            found_modification = at.traffic_elements[0].switch_modifications[mf][1]
            self.assertEqual(expected_modified_fields[mf], found_modification)

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

        test_port = swpg.sw.ports[primary_egress_port_num]
        test_port.state = "down"
        swpg.update_admitted_traffic_due_to_port_state_change(primary_egress_port_num, "port_down")

        failover_at_int, ingress_node, egress_node = self.check_admitted_traffic(swpg, src_host_obj,
                                                                                 dst_host_obj,
                                                                                 ingress_port_num,
                                                                                 failover_egress_port_num)

        self.check_path(swpg, primary_at_int, ingress_node, egress_node, failover_expected_path)

        test_port.state = "up"
        swpg.update_admitted_traffic_due_to_port_state_change(primary_egress_port_num, "port_up")

        return primary_at_int, failover_at_int

    def test_linear_dijkstra_admitted_traffic(self):
        h1_obj = self.ng_linear_dijkstra.get_node_object("h1")
        h2_obj = self.ng_linear_dijkstra.get_node_object("h2")

        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.swpg_linear_dijkstra, h1_obj, h2_obj, 1, 2)

    def test_linear_dijkstra_modifications(self):
        h1_obj = self.ng_linear_dijkstra.get_node_object("h1")
        h2_obj = self.ng_linear_dijkstra.get_node_object("h2")

        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.swpg_linear_dijkstra, h1_obj, h2_obj, 1, 2)
        self.check_modifications(at_int, {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(4098, 4099)})

    def test_linear_dijkstra_paths(self):
        h1_obj = self.ng_linear_dijkstra.get_node_object("h1")
        h2_obj = self.ng_linear_dijkstra.get_node_object("h2")
        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.swpg_linear_dijkstra, h1_obj, h2_obj, 1, 2)

        expected_path = TrafficPath(self.swpg_linear_dijkstra,
                                    [self.swpg_linear_dijkstra.get_node("s1:ingress1"),
                                     self.swpg_linear_dijkstra.get_node("s1:table0"),
                                     self.swpg_linear_dijkstra.get_node("s1:table1"),
                                     self.swpg_linear_dijkstra.get_node("s1:table2"),
                                     self.swpg_linear_dijkstra.get_node("s1:egress2")])

        self.check_path(self.swpg_linear_dijkstra, at_int, ingress_node, egress_node, expected_path)

    def test_ring_aborescene_admitted_traffic(self):

        # This test asserts that in switch s1, for host h11, with no failures:
        # Traffic for host h21 flows out of port 3
        # Traffic for host h31 flows out of port 2
        # Traffic for host h41 flows out of port 2

        h11_obj = self.ng_ring_aborescene_apply_true.get_node_object("h11")
        h21_obj = self.ng_ring_aborescene_apply_true.get_node_object("h21")
        h31_obj = self.ng_ring_aborescene_apply_true.get_node_object("h31")
        h41_obj = self.ng_ring_aborescene_apply_true.get_node_object("h41")

        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.swpg_ring_aborescene_apply_true,
                                                                        h11_obj, h21_obj, 1, 3)
        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.swpg_ring_aborescene_apply_true,
                                                                        h11_obj, h31_obj, 1, 2)
        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.swpg_ring_aborescene_apply_true,
                                                                        h11_obj, h41_obj, 1, 2)

        # This test asserts that in switch s1, for host h11, with no failures:
        # Traffic for host h21 flows out of port 3
        # Traffic for host h31 flows out of port 2
        # Traffic for host h41 flows out of port 2

        h11_obj = self.ng_ring_aborescene_apply_false.get_node_object("h11")
        h21_obj = self.ng_ring_aborescene_apply_false.get_node_object("h21")
        h31_obj = self.ng_ring_aborescene_apply_false.get_node_object("h31")
        h41_obj = self.ng_ring_aborescene_apply_false.get_node_object("h41")

        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.swpg_ring_aborescene_apply_false,
                                                                        h11_obj, h21_obj, 1, 3)
        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.swpg_ring_aborescene_apply_false,
                                                                        h11_obj, h31_obj, 1, 2)
        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.swpg_ring_aborescene_apply_false,
                                                                        h11_obj, h41_obj, 1, 2)


    def test_ring_aborescene_modifications(self):

        # This test asserts that in switch s1, for host h11, with no failures:
        # Traffic for host h21 flows out of port 3 with modifications 5122
        # Traffic for host h31 flows out of port 2 with modifications 5123
        # Traffic for host h41 flows out of port 2 with modifications 5124

        h11_obj = self.ng_ring_aborescene_apply_true.get_node_object("h11")
        h21_obj = self.ng_ring_aborescene_apply_true.get_node_object("h21")
        h31_obj = self.ng_ring_aborescene_apply_true.get_node_object("h31")
        h41_obj = self.ng_ring_aborescene_apply_true.get_node_object("h41")

        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.swpg_ring_aborescene_apply_true,
                                                                        h11_obj, h21_obj, 1, 3)
        self.check_modifications(at_int, {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(5122, 5123)})

        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.swpg_ring_aborescene_apply_true,
                                                                        h11_obj, h31_obj, 1, 2)
        self.check_modifications(at_int, {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(5123, 5124)})

        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.swpg_ring_aborescene_apply_true,
                                                                        h11_obj, h41_obj, 1, 2)
        self.check_modifications(at_int, {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(5124, 5125)})

        # This test asserts that in switch s1, for host h11, with no failures:
        # Traffic for host h21 flows out of port 3 with modifications 5122
        # Traffic for host h31 flows out of port 2 with modifications 5123
        # Traffic for host h41 flows out of port 2 with modifications 5124

        h11_obj = self.ng_ring_aborescene_apply_false.get_node_object("h11")
        h21_obj = self.ng_ring_aborescene_apply_false.get_node_object("h21")
        h31_obj = self.ng_ring_aborescene_apply_false.get_node_object("h31")
        h41_obj = self.ng_ring_aborescene_apply_false.get_node_object("h41")

        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.swpg_ring_aborescene_apply_false,
                                                                        h11_obj, h21_obj, 1, 3)
        self.check_modifications(at_int, {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(5122, 5123)})

        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.swpg_ring_aborescene_apply_false,
                                                                        h11_obj, h31_obj, 1, 2)
        self.check_modifications(at_int, {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(5123, 5124)})

        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.swpg_ring_aborescene_apply_false,
                                                                        h11_obj, h41_obj, 1, 2)
        self.check_modifications(at_int, {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(5124, 5125)})

    def test_ring_aborescene_paths(self):

        # This test asserts that in switch s1, for host h11, with no failures:
        # Traffic for host h21 flows out of port 3 via the specified path below
        # Traffic for host h31 flows out of port 2 via the specified path below
        # Traffic for host h41 flows out of port 2 via the specified path below

        h11_obj = self.ng_ring_aborescene_apply_true.get_node_object("h11")
        h21_obj = self.ng_ring_aborescene_apply_true.get_node_object("h21")
        h31_obj = self.ng_ring_aborescene_apply_true.get_node_object("h31")
        h41_obj = self.ng_ring_aborescene_apply_true.get_node_object("h41")

        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.swpg_ring_aborescene_apply_true,
                                                                        h11_obj, h21_obj, 1, 3)
        expected_path = TrafficPath(self.swpg_ring_aborescene_apply_true,
                                    [self.swpg_ring_aborescene_apply_true.get_node("s1:ingress1"),
                                     self.swpg_ring_aborescene_apply_true.get_node("s1:table0"),
                                     self.swpg_ring_aborescene_apply_true.get_node("s1:table1"),
                                     self.swpg_ring_aborescene_apply_true.get_node("s1:table2"),
                                     self.swpg_ring_aborescene_apply_true.get_node("s1:table3"),
                                     self.swpg_ring_aborescene_apply_true.get_node("s1:egress3")])
        self.check_path(self.swpg_ring_aborescene_apply_true, at_int, ingress_node, egress_node, expected_path)

        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.swpg_ring_aborescene_apply_true,
                                                                        h11_obj, h31_obj, 1, 2)
        expected_path = TrafficPath(self.swpg_ring_aborescene_apply_true,
                                    [self.swpg_ring_aborescene_apply_true.get_node("s1:ingress1"),
                                     self.swpg_ring_aborescene_apply_true.get_node("s1:table0"),
                                     self.swpg_ring_aborescene_apply_true.get_node("s1:table1"),
                                     self.swpg_ring_aborescene_apply_true.get_node("s1:table2"),
                                     self.swpg_ring_aborescene_apply_true.get_node("s1:table3"),
                                     self.swpg_ring_aborescene_apply_true.get_node("s1:egress2")])
        self.check_path(self.swpg_ring_aborescene_apply_true, at_int, ingress_node, egress_node, expected_path)

        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.swpg_ring_aborescene_apply_true,
                                                                        h11_obj, h41_obj, 1, 2)
        expected_path = TrafficPath(self.swpg_ring_aborescene_apply_true,
                                    [self.swpg_ring_aborescene_apply_true.get_node("s1:ingress1"),
                                     self.swpg_ring_aborescene_apply_true.get_node("s1:table0"),
                                     self.swpg_ring_aborescene_apply_true.get_node("s1:table1"),
                                     self.swpg_ring_aborescene_apply_true.get_node("s1:table2"),
                                     self.swpg_ring_aborescene_apply_true.get_node("s1:table3"),
                                     self.swpg_ring_aborescene_apply_true.get_node("s1:egress2")])
        self.check_path(self.swpg_ring_aborescene_apply_true, at_int, ingress_node, egress_node, expected_path)

        # This test asserts that in switch s1, for host h11, with no failures:
        # Traffic for host h21 flows out of port 3 via the specified path below
        # Traffic for host h31 flows out of port 2 via the specified path below
        # Traffic for host h41 flows out of port 2 via the specified path below

        h11_obj = self.ng_ring_aborescene_apply_false.get_node_object("h11")
        h21_obj = self.ng_ring_aborescene_apply_false.get_node_object("h21")
        h31_obj = self.ng_ring_aborescene_apply_false.get_node_object("h31")
        h41_obj = self.ng_ring_aborescene_apply_false.get_node_object("h41")

        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.swpg_ring_aborescene_apply_false,
                                                                        h11_obj, h21_obj, 1, 3)
        expected_path = TrafficPath(self.swpg_ring_aborescene_apply_false,
                                    [self.swpg_ring_aborescene_apply_false.get_node("s1:ingress1"),
                                     self.swpg_ring_aborescene_apply_false.get_node("s1:table0"),
                                     self.swpg_ring_aborescene_apply_false.get_node("s1:table1"),
                                     self.swpg_ring_aborescene_apply_false.get_node("s1:table2"),
                                     self.swpg_ring_aborescene_apply_false.get_node("s1:table3"),
                                     self.swpg_ring_aborescene_apply_false.get_node("s1:egress3")])
        self.check_path(self.swpg_ring_aborescene_apply_false, at_int, ingress_node, egress_node, expected_path)

        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.swpg_ring_aborescene_apply_false,
                                                                        h11_obj, h31_obj, 1, 2)
        expected_path = TrafficPath(self.swpg_ring_aborescene_apply_false,
                                    [self.swpg_ring_aborescene_apply_false.get_node("s1:ingress1"),
                                     self.swpg_ring_aborescene_apply_false.get_node("s1:table0"),
                                     self.swpg_ring_aborescene_apply_false.get_node("s1:table1"),
                                     self.swpg_ring_aborescene_apply_false.get_node("s1:table2"),
                                     self.swpg_ring_aborescene_apply_false.get_node("s1:table3"),
                                     self.swpg_ring_aborescene_apply_false.get_node("s1:egress2")])
        self.check_path(self.swpg_ring_aborescene_apply_false, at_int, ingress_node, egress_node, expected_path)

        at_int, ingress_node, egress_node = self.check_admitted_traffic(self.swpg_ring_aborescene_apply_false,
                                                                        h11_obj, h41_obj, 1, 2)
        expected_path = TrafficPath(self.swpg_ring_aborescene_apply_false,
                                    [self.swpg_ring_aborescene_apply_false.get_node("s1:ingress1"),
                                     self.swpg_ring_aborescene_apply_false.get_node("s1:table0"),
                                     self.swpg_ring_aborescene_apply_false.get_node("s1:table1"),
                                     self.swpg_ring_aborescene_apply_false.get_node("s1:table2"),
                                     self.swpg_ring_aborescene_apply_false.get_node("s1:table3"),
                                     self.swpg_ring_aborescene_apply_false.get_node("s1:egress2")])
        self.check_path(self.swpg_ring_aborescene_apply_false, at_int, ingress_node, egress_node, expected_path)

    def test_ring_aborescene_admitted_traffic_failover(self):

        # This test asserts that in switch s1, for host h11, with a single failures:
        # Traffic for host h21 flows out of port 3 before failure and out of port 2 after failure
        # Traffic for host h31 flows out of port 2 before failure and out of port 3 after failure
        # Traffic for host h41 flows out of port 2 before failure and out of port 3 after failure

        h11_obj = self.ng_ring_aborescene_apply_true.get_node_object("h11")
        h21_obj = self.ng_ring_aborescene_apply_true.get_node_object("h21")
        h31_obj = self.ng_ring_aborescene_apply_true.get_node_object("h31")
        h41_obj = self.ng_ring_aborescene_apply_true.get_node_object("h41")

        self.check_failover_admitted_traffic(self.swpg_ring_aborescene_apply_true, h11_obj, h21_obj, 1, 3, 2)
        self.check_failover_admitted_traffic(self.swpg_ring_aborescene_apply_true, h11_obj, h31_obj, 1, 2, 3)
        self.check_failover_admitted_traffic(self.swpg_ring_aborescene_apply_true, h11_obj, h41_obj, 1, 2, 3)

        # This test asserts that in switch s1, for host h11, with a single failures:
        # Traffic for host h21 flows out of port 3 before failure and out of port 2 after failure
        # Traffic for host h31 flows out of port 2 before failure and out of port 3 after failure
        # Traffic for host h41 flows out of port 2 before failure and out of port 3 after failure

        h11_obj = self.ng_ring_aborescene_apply_false.get_node_object("h11")
        h21_obj = self.ng_ring_aborescene_apply_false.get_node_object("h21")
        h31_obj = self.ng_ring_aborescene_apply_false.get_node_object("h31")
        h41_obj = self.ng_ring_aborescene_apply_false.get_node_object("h41")

        self.check_failover_admitted_traffic(self.swpg_ring_aborescene_apply_false, h11_obj, h21_obj, 1, 3, 2)
        self.check_failover_admitted_traffic(self.swpg_ring_aborescene_apply_false, h11_obj, h31_obj, 1, 2, 3)
        self.check_failover_admitted_traffic(self.swpg_ring_aborescene_apply_false, h11_obj, h41_obj, 1, 2, 3)

    def test_ring_aborescene_modifications_failover(self):

        # This test asserts that in switch s1, for host h11, with a single failures:
        # Traffic for host h21 flows out of port 3 with modifications 5122 before failure and
        # out of port 2 with modifications 6146 after failure
        # Traffic for host h31 flows out of port 2 with modifications 5123 before failure and
        # out of port 3 with modifications 6147 after failure
        # Traffic for host h41 flows out of port 2 with modifications 5124 before failure and
        # out of port 3 with modifications 6148 after failure

        h11_obj = self.ng_ring_aborescene_apply_true.get_node_object("h11")
        h21_obj = self.ng_ring_aborescene_apply_true.get_node_object("h21")
        h31_obj = self.ng_ring_aborescene_apply_true.get_node_object("h31")
        h41_obj = self.ng_ring_aborescene_apply_true.get_node_object("h41")

        primary_at, failover_at = self.check_failover_admitted_traffic(self.swpg_ring_aborescene_apply_true,
                                                                       h11_obj, h21_obj, 1, 3, 2)
        self.check_failover_modifications(primary_at, failover_at,
                                          {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(5122, 5123)},
                                          {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(6146, 6147)})

        primary_at, failover_at = self.check_failover_admitted_traffic(self.swpg_ring_aborescene_apply_true,
                                                                       h11_obj, h31_obj, 1, 2, 3)
        self.check_failover_modifications(primary_at, failover_at,
                                          {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(5123, 5124)},
                                          {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(6147, 6148)})

        primary_at, failover_at = self.check_failover_admitted_traffic(self.swpg_ring_aborescene_apply_true,
                                                                       h11_obj, h41_obj, 1, 2, 3)
        self.check_failover_modifications(primary_at, failover_at,
                                          {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(5124, 5125)},
                                          {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(6148, 6149)})

        # This test asserts that in switch s1, for host h11, with a single failures:
        # Traffic for host h21 flows out of port 3 with modifications 5122 before failure and
        # out of port 2 with modifications 6146 after failure
        # Traffic for host h31 flows out of port 2 with modifications 5123 before failure and
        # out of port 3 with modifications 6147 after failure
        # Traffic for host h41 flows out of port 2 with modifications 5124 before failure and
        # out of port 3 with modifications 6148 after failure

        h11_obj = self.ng_ring_aborescene_apply_false.get_node_object("h11")
        h21_obj = self.ng_ring_aborescene_apply_false.get_node_object("h21")
        h31_obj = self.ng_ring_aborescene_apply_false.get_node_object("h31")
        h41_obj = self.ng_ring_aborescene_apply_false.get_node_object("h41")

        primary_at, failover_at = self.check_failover_admitted_traffic(self.swpg_ring_aborescene_apply_false,
                                                                       h11_obj, h21_obj, 1, 3, 2)
        self.check_failover_modifications(primary_at, failover_at,
                                          {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(5122, 5123)},
                                          {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(6146, 6147)})

        primary_at, failover_at = self.check_failover_admitted_traffic(self.swpg_ring_aborescene_apply_false,
                                                                       h11_obj, h31_obj, 1, 2, 3)
        self.check_failover_modifications(primary_at, failover_at,
                                          {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(5123, 5124)},
                                          {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(6147, 6148)})

        primary_at, failover_at = self.check_failover_admitted_traffic(self.swpg_ring_aborescene_apply_false,
                                                                       h11_obj, h41_obj, 1, 2, 3)
        self.check_failover_modifications(primary_at, failover_at,
                                          {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(5124, 5125)},
                                          {"has_vlan_tag": Interval(1, 2), "vlan_id": Interval(6148, 6149)})

    def test_ring_aborescene_paths_failover(self):

        # This test asserts that in switch s1, for host h11, with a single failures:
        # Traffic for host h21 flows out of port 3 before failure and out of port 2 after failure
        # Traffic for host h31 flows out of port 2 before failure and out of port 3 after failure
        # Traffic for host h41 flows out of port 2 before failure and out of port 3 after failure

        h11_obj = self.ng_ring_aborescene_apply_true.get_node_object("h11")
        h21_obj = self.ng_ring_aborescene_apply_true.get_node_object("h21")
        h31_obj = self.ng_ring_aborescene_apply_true.get_node_object("h31")
        h41_obj = self.ng_ring_aborescene_apply_true.get_node_object("h41")

        expected_path_via_egress2 = TrafficPath(self.swpg_ring_aborescene_apply_true,
                                                [self.swpg_ring_aborescene_apply_true.get_node("s1:ingress1"),
                                                 self.swpg_ring_aborescene_apply_true.get_node("s1:table0"),
                                                 self.swpg_ring_aborescene_apply_true.get_node("s1:table1"),
                                                 self.swpg_ring_aborescene_apply_true.get_node("s1:table2"),
                                                 self.swpg_ring_aborescene_apply_true.get_node("s1:table3"),
                                                 self.swpg_ring_aborescene_apply_true.get_node("s1:egress2")])

        expected_path_via_egress3 = TrafficPath(self.swpg_ring_aborescene_apply_true,
                                                [self.swpg_ring_aborescene_apply_true.get_node("s1:ingress1"),
                                                 self.swpg_ring_aborescene_apply_true.get_node("s1:table0"),
                                                 self.swpg_ring_aborescene_apply_true.get_node("s1:table1"),
                                                 self.swpg_ring_aborescene_apply_true.get_node("s1:table2"),
                                                 self.swpg_ring_aborescene_apply_true.get_node("s1:table3"),
                                                 self.swpg_ring_aborescene_apply_true.get_node("s1:egress3")])

        self.check_failover_path(self.swpg_ring_aborescene_apply_true, h11_obj, h21_obj, 1, 3, 2,
                                 expected_path_via_egress3, expected_path_via_egress2)

        self.check_failover_path(self.swpg_ring_aborescene_apply_true, h11_obj, h31_obj, 1, 2, 3,
                                 expected_path_via_egress2, expected_path_via_egress3)

        self.check_failover_path(self.swpg_ring_aborescene_apply_true, h11_obj, h41_obj, 1, 2, 3,
                                 expected_path_via_egress2, expected_path_via_egress3)

        # This test asserts that in switch s1, for host h11, with a single failures:
        # Traffic for host h21 flows out of port 3 before failure and out of port 2 after failure
        # Traffic for host h31 flows out of port 2 before failure and out of port 3 after failure
        # Traffic for host h41 flows out of port 2 before failure and out of port 3 after failure

        h11_obj = self.ng_ring_aborescene_apply_false.get_node_object("h11")
        h21_obj = self.ng_ring_aborescene_apply_false.get_node_object("h21")
        h31_obj = self.ng_ring_aborescene_apply_false.get_node_object("h31")
        h41_obj = self.ng_ring_aborescene_apply_false.get_node_object("h41")

        expected_path_via_egress2 = TrafficPath(self.swpg_ring_aborescene_apply_false,
                                                [self.swpg_ring_aborescene_apply_false.get_node("s1:ingress1"),
                                                 self.swpg_ring_aborescene_apply_false.get_node("s1:table0"),
                                                 self.swpg_ring_aborescene_apply_false.get_node("s1:table1"),
                                                 self.swpg_ring_aborescene_apply_false.get_node("s1:table2"),
                                                 self.swpg_ring_aborescene_apply_false.get_node("s1:table3"),
                                                 self.swpg_ring_aborescene_apply_false.get_node("s1:egress2")])

        expected_path_via_egress3 = TrafficPath(self.swpg_ring_aborescene_apply_false,
                                                [self.swpg_ring_aborescene_apply_false.get_node("s1:ingress1"),
                                                 self.swpg_ring_aborescene_apply_false.get_node("s1:table0"),
                                                 self.swpg_ring_aborescene_apply_false.get_node("s1:table1"),
                                                 self.swpg_ring_aborescene_apply_false.get_node("s1:table2"),
                                                 self.swpg_ring_aborescene_apply_false.get_node("s1:table3"),
                                                 self.swpg_ring_aborescene_apply_false.get_node("s1:egress3")])

        self.check_failover_path(self.swpg_ring_aborescene_apply_false, h11_obj, h21_obj, 1, 3, 2,
                                 expected_path_via_egress3, expected_path_via_egress2)

        self.check_failover_path(self.swpg_ring_aborescene_apply_false, h11_obj, h31_obj, 1, 2, 3,
                                 expected_path_via_egress2, expected_path_via_egress3)

        self.check_failover_path(self.swpg_ring_aborescene_apply_false, h11_obj, h41_obj, 1, 2, 3,
                                 expected_path_via_egress2, expected_path_via_egress3)

if __name__ == '__main__':
    unittest.main()
