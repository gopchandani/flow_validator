import unittest

from traffic import Traffic
from network_graph import NetworkGraph
from network_port_graph import NetworkPortGraph

from experiments.network_configuration import NetworkConfiguration


class TestNetworkPortGraph(unittest.TestCase):

    def setUp(self):
        nc = NetworkConfiguration("ryu",
                                  "ring",
                                  {"num_switches": 4,
                                   "num_hosts_per_switch": 1},
                                  load_config=True,
                                  save_config=False,
                                  synthesis_scheme="Synthesis_Failover_Aborescene")

        self.ng = NetworkGraph(nc)
        sw = self.ng.get_node_object("s1")
        self.ring_npg = NetworkPortGraph(self.ng, True)
        self.ring_npg.init_network_port_graph()

        # Attach a destination port for each host.
        for host_id in self.ng.host_ids:

            host_obj = self.ng.get_node_object(host_id)
            host_obj.switch_ingress_port = self.ring_npg.get_node(host_obj.switch_id +
                                                                  ":ingress" + str(host_obj.switch_port_attached))
            host_obj.switch_egress_port = self.ring_npg.get_node(host_obj.switch_id +
                                                                 ":egress" + str(host_obj.switch_port_attached))
        # Initialize traffic from each host node as well
        for host_id in self.ng.host_ids:
            host_obj = self.ng.get_node_object(host_id)

            dst_traffic_at_succ = Traffic(init_wildcard=True)
            dst_traffic_at_succ.set_field("ethernet_type", 0x0800)
            dst_mac_int = int(host_obj.mac_addr.replace(":", ""), 16)
            dst_traffic_at_succ.set_field("ethernet_destination", dst_mac_int)

            print "Initializing for host:", host_id

            end_to_end_modified_edges = []

            self.ring_npg.propagate_admitted_traffic(host_obj.switch_egress_port,
                                                     dst_traffic_at_succ,
                                                     None,
                                                     host_obj.switch_egress_port,
                                                     end_to_end_modified_edges)

    def test_two_link_failure_modification_change(self):

        # Initialize some data structures
        src_h_obj = self.ng.get_node_object("h21")
        dst_h_obj = self.ng.get_node_object("h31")

        specific_traffic = Traffic(init_wildcard=True)
        specific_traffic.set_field("ethernet_type", 0x0800)
        specific_traffic.set_field("ethernet_source", int(src_h_obj.mac_addr.replace(":", ""), 16))
        specific_traffic.set_field("ethernet_destination", int(dst_h_obj.mac_addr.replace(":", ""), 16))
        specific_traffic.set_field("in_port", int(src_h_obj.switch_port_attached))
        specific_traffic.set_field("vlan_id", src_h_obj.switch_obj.synthesis_tag + 0x1000, is_exception_value=True)
        specific_traffic.set_field("has_vlan_tag", 0)

        src_node = self.ring_npg.get_ingress_node("s2", 1)
        dst_node = self.ring_npg.get_egress_node("s3", 1)
        egress_node_2 = self.ring_npg.get_egress_node("s2", 2)
        egress_node_3 = self.ring_npg.get_egress_node("s2", 3)

        # Delete the first link and measure
        self.ring_npg.remove_node_graph_link("s1", "s4")
        before_at = self.ring_npg.get_admitted_traffic_via_succ(src_node, dst_node, egress_node_3)
        before_at_int = specific_traffic.intersect(before_at)

        # Delete the second link
        self.ring_npg.remove_node_graph_link("s2", "s3")
        after_at = self.ring_npg.get_admitted_traffic_via_succ(src_node, dst_node, egress_node_2)
        after_at_int = specific_traffic.intersect(after_at)

        is_traffic_equal = before_at_int.is_equal_traffic(after_at_int)
        self.assertEqual(is_traffic_equal, True)


if __name__ == '__main__':
    unittest.main()
