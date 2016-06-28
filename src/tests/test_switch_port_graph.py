import unittest
import os
from model.switch_port_graph import SwitchPortGraph
from model.traffic import Traffic

from experiments.network_configuration import NetworkConfiguration


class TestSwitchPortGraph(unittest.TestCase):

    def setUp(self):

        nc = NetworkConfiguration("ryu",
                                  "ring",
                                  {"num_switches": 4,
                                   "num_hosts_per_switch": 1},
                                  load_config=False,
                                  save_config=True,
                                  conf_root=os.path.dirname(__file__) + "/",
                                  synthesis_name="AboresceneSynthesis",
                                  synthesis_params={"apply_group_intents_immediately": True})

        self.ng = nc.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)
        sw = self.ng.get_node_object("s1")
        self.ring_swpg = SwitchPortGraph(self.ng, sw, True)
        sw.port_graph = self.ring_swpg
        self.ring_swpg.init_switch_port_graph()
        self.ring_swpg.compute_switch_admitted_traffic()

    def test_single_port_failure(self, verbose=False):

        src_h_obj = self.ng.get_node_object("h11")
        dst_h_obj = self.ng.get_node_object("h21")

        specific_traffic = Traffic(init_wildcard=True)
        specific_traffic.set_field("ethernet_type", 0x0800)
        specific_traffic.set_field("ethernet_source", int(src_h_obj.mac_addr.replace(":", ""), 16))
        specific_traffic.set_field("ethernet_destination", int(dst_h_obj.mac_addr.replace(":", ""), 16))
        specific_traffic.set_field("in_port", int(src_h_obj.switch_port_attached))
        specific_traffic.set_field("vlan_id", src_h_obj.switch_obj.synthesis_tag + 0x1000, is_exception_value=True)
        specific_traffic.set_field("has_vlan_tag", 0)

        ingress_node_1 = self.ring_swpg.get_ingress_node("s1", 1)
        egress_node_2 = self.ring_swpg.get_egress_node("s1", 2)
        egress_node_3 = self.ring_swpg.get_egress_node("s1", 3)

        before_at = self.ring_swpg.get_admitted_traffic(ingress_node_1, egress_node_3)
        before_at_int = specific_traffic.intersect(before_at)

        testing_port_number = 3
        testing_port = self.ring_swpg.sw.ports[testing_port_number]
        testing_port.state = "down"
        end_to_end_modified_edges = self.ring_swpg.update_admitted_traffic_due_to_port_state_change(testing_port_number,
                                                                                               "port_down")
        after_at = self.ring_swpg.get_admitted_traffic(ingress_node_1, egress_node_2)
        after_at_int = specific_traffic.intersect(after_at)

        is_traffic_equal = before_at_int.is_equal_traffic(after_at_int)

        self.assertEqual(is_traffic_equal, True)

    def test_one_port_failure_at_a_time(self, verbose=False):

        test_passed = True

        # Loop over ports of the switch and fail and restore them one by one
        for testing_port_number in self.ring_swpg.sw.ports:

            print "testing_port_number:", testing_port_number

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
                print "Test Failed."

            all_graph_ats_equal = self.ring_swpg.compare_graph_ats(graph_ats_before,
                                                              graph_ats_after,
                                                              verbose)
            if not all_graph_ats_equal:
                test_passed = all_graph_ats_equal
                print "Test Failed."

        self.assertEqual(test_passed, True)

if __name__ == '__main__':
    unittest.main()
