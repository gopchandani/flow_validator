import unittest
import os

from model.traffic import Traffic
from model.network_port_graph import NetworkPortGraph
from experiments.network_configuration import NetworkConfiguration


class TestNetworkPortGraph(unittest.TestCase):

    @classmethod
    def attach_hosts_port_nodes_with_npg(cls, ng, npg):

        # Attach a destination port for each host.
        for host_id in ng.host_ids:

            host_obj = ng.get_node_object(host_id)
            host_obj.switch_ingress_port = npg.get_node(host_obj.switch_id +
                                                        ":ingress" +
                                                        str(host_obj.switch_port_attached))
            host_obj.switch_egress_port = npg.get_node(host_obj.switch_id +
                                                       ":egress" +
                                                       str(host_obj.switch_port_attached))
    @classmethod
    def init_hosts_traffic_propagation(cls, ng, npg):
        for host_id in ng.host_ids:
            host_obj = ng.get_node_object(host_id)

            dst_traffic_at_succ = Traffic(init_wildcard=True)
            dst_traffic_at_succ.set_field("ethernet_type", 0x0800)
            dst_mac_int = int(host_obj.mac_addr.replace(":", ""), 16)
            dst_traffic_at_succ.set_field("ethernet_destination", dst_mac_int)

            print "Initializing for host:", host_id

            end_to_end_modified_edges = []

            npg.propagate_admitted_traffic(host_obj.switch_egress_port,
                                           dst_traffic_at_succ,
                                           None,
                                           host_obj.switch_egress_port,
                                           end_to_end_modified_edges)

    @classmethod
    def setUpClass(cls):

        cls.nc_ring_aborescene_apply_true = NetworkConfiguration("ryu",
                                                                 "ring",
                                                                 {"num_switches": 4,
                                                                  "num_hosts_per_switch": 1},
                                                                 conf_root=os.path.dirname(__file__) + "/",
                                                                 synthesis_name="AboresceneSynthesis",
                                                                 synthesis_params={"apply_group_intents_immediately":
                                                                                       True})

        cls.ng_ring_aborescene_apply_true = cls.nc_ring_aborescene_apply_true.setup_network_graph(mininet_setup_gap=1,
                                                                                                  synthesis_setup_gap=1)
        cls.npg_ring_aborescene_apply_true = NetworkPortGraph(cls.ng_ring_aborescene_apply_true, True)
        cls.npg_ring_aborescene_apply_true.init_network_port_graph()

        cls.attach_hosts_port_nodes_with_npg(cls.ng_ring_aborescene_apply_true, cls.npg_ring_aborescene_apply_true)
        cls.init_hosts_traffic_propagation(cls.ng_ring_aborescene_apply_true, cls.npg_ring_aborescene_apply_true)

    def check_two_link_failure_admitted_traffic_absence(self, npg, src_h_obj, dst_h_obj, links_to_fail):

        specific_traffic = Traffic(init_wildcard=True)
        specific_traffic.set_field("ethernet_type", 0x0800)
        specific_traffic.set_field("ethernet_source", int(src_h_obj.mac_addr.replace(":", ""), 16))
        specific_traffic.set_field("ethernet_destination", int(dst_h_obj.mac_addr.replace(":", ""), 16))
        specific_traffic.set_field("in_port", int(src_h_obj.switch_port_attached))
        specific_traffic.set_field("vlan_id", src_h_obj.switch_obj.synthesis_tag + 0x1000, is_exception_value=True)
        specific_traffic.set_field("has_vlan_tag", 0)

        before_at = npg.get_admitted_traffic(src_h_obj.switch_ingress_port, dst_h_obj.switch_egress_port)

        for link_to_fail in links_to_fail:
            npg.remove_node_graph_link(*link_to_fail)

        after_at = npg.get_admitted_traffic(src_h_obj.switch_ingress_port, dst_h_obj.switch_egress_port)
        self.assertEqual(after_at.is_empty(), True)

    def test_two_link_failure_admitted_traffic_absence(self):

        # Initialize some data structures
        src_h_obj = self.ng_ring_aborescene_apply_true.get_node_object("h21")
        dst_h_obj = self.ng_ring_aborescene_apply_true.get_node_object("h31")
        links_to_fail = [("s1", "s4"), ("s2", "s3")]

        self.check_two_link_failure_admitted_traffic_absence(self.npg_ring_aborescene_apply_true,
                                                             src_h_obj, dst_h_obj, links_to_fail)

if __name__ == '__main__':
    unittest.main()
