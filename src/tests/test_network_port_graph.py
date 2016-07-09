import unittest
import os
import json

from collections import defaultdict
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

        cls.npg_ring_aborescene_apply_true_report_active_false = NetworkPortGraph(cls.ng_ring_aborescene_apply_true,
                                                                                  False)
        cls.npg_ring_aborescene_apply_true_report_active_false.init_network_port_graph()
        cls.attach_hosts_port_nodes_with_npg(cls.ng_ring_aborescene_apply_true,
                                             cls.npg_ring_aborescene_apply_true_report_active_false)
        cls.init_hosts_traffic_propagation(cls.ng_ring_aborescene_apply_true,
                                           cls.npg_ring_aborescene_apply_true_report_active_false)

        cls.nc_clos_dijkstra = NetworkConfiguration("ryu",
                                                    "clostopo",
                                                    {"fanout": 2,
                                                     "core": 1,
                                                     "num_hosts_per_switch": 1},
                                                    conf_root=os.path.dirname(__file__) + "/",
                                                    synthesis_name="DijkstraSynthesis",
                                                    synthesis_params={})
        cls.ng_clos_dijkstra = cls.nc_clos_dijkstra.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

        cls.npg_clos_dijkstra = NetworkPortGraph(cls.ng_clos_dijkstra, True)
        cls.npg_clos_dijkstra.init_network_port_graph()
        cls.attach_hosts_port_nodes_with_npg(cls.ng_clos_dijkstra, cls.npg_clos_dijkstra)
        cls.init_hosts_traffic_propagation(cls.ng_clos_dijkstra, cls.npg_clos_dijkstra)

        cls.npg_clos_dijkstra_report_active_false = NetworkPortGraph(cls.ng_clos_dijkstra, False)
        cls.npg_clos_dijkstra_report_active_false.init_network_port_graph()
        cls.attach_hosts_port_nodes_with_npg(cls.ng_clos_dijkstra, cls.npg_clos_dijkstra_report_active_false)
        cls.init_hosts_traffic_propagation(cls.ng_clos_dijkstra, cls.npg_clos_dijkstra_report_active_false)

    def check_single_link_failure_admitted_traffic_subset(self, npg, node, dst, traffic_to_check, link_to_fail):

        npg.remove_node_graph_link(*link_to_fail)
        after_at = npg.get_admitted_traffic(node, dst)

        is_subset = after_at.is_subset_traffic(traffic_to_check)

        self.assertEqual(is_subset, True)
        npg.add_node_graph_link(*link_to_fail, updating=True)

    def check_single_link_failure_admitted_traffic_match(self, npg, node, dst, traffic_to_match, link_to_fail):

        npg.remove_node_graph_link(*link_to_fail)
        after_at = npg.get_admitted_traffic(node, dst)
        self.assertEqual(after_at, traffic_to_match)
        npg.add_node_graph_link(*link_to_fail, updating=True)

    def check_two_link_failure_admitted_traffic_absence(self, npg, src_h_obj, dst_h_obj, links_to_fail):

        for link_to_fail in links_to_fail:
            before_at = npg.get_admitted_traffic(src_h_obj.switch_ingress_port, dst_h_obj.switch_egress_port)
            all_paths = npg.get_paths(src_h_obj.switch_ingress_port,
                                      dst_h_obj.switch_egress_port,
                                      before_at,
                                      [src_h_obj.switch_ingress_port],
                                      [],
                                      True)

            npg.remove_node_graph_link(*link_to_fail)

        after_at = npg.get_admitted_traffic(src_h_obj.switch_ingress_port, dst_h_obj.switch_egress_port)
        all_paths = npg.get_paths(src_h_obj.switch_ingress_port,
                                  dst_h_obj.switch_egress_port,
                                  after_at,
                                  [src_h_obj.switch_ingress_port],
                                  [],
                                  True)

        for link_to_fail in links_to_fail:
            npg.add_node_graph_link(*link_to_fail, updating=True)

        self.assertEqual(after_at.is_empty(), True)

    def get_specific_traffic(self, ng, src_h_id, dst_h_id):

        src_h_obj = ng.get_node_object(src_h_id)
        dst_h_obj = ng.get_node_object(dst_h_id)

        specific_traffic = Traffic(init_wildcard=True)
        specific_traffic.set_field("ethernet_type", 0x0800)
        specific_traffic.set_field("ethernet_source", int(src_h_obj.mac_addr.replace(":", ""), 16))
        specific_traffic.set_field("ethernet_destination", int(dst_h_obj.mac_addr.replace(":", ""), 16))
        specific_traffic.set_field("in_port", int(src_h_obj.switch_port_attached))
        specific_traffic.set_field("vlan_id", src_h_obj.switch_obj.synthesis_tag + 0x1000, is_exception_value=True)
        specific_traffic.set_field("has_vlan_tag", 0)

        return specific_traffic

    def get_all_host_pairs_traffic_paths(self, ng, npg, verbose=False):

        host_pair_paths = defaultdict(defaultdict)

        for src_h_id in ng.host_ids:
            for dst_h_id in ng.host_ids:

                if src_h_id == dst_h_id:
                    continue

                specific_traffic = self.get_specific_traffic(ng, src_h_id, dst_h_id)

                src_host_obj = ng.get_node_object(src_h_id)
                dst_host_obj = ng.get_node_object(dst_h_id)

                all_paths = npg.get_paths(src_host_obj.switch_ingress_port,
                                          dst_host_obj.switch_egress_port,
                                          specific_traffic,
                                          [src_host_obj.switch_ingress_port],
                                          [],
                                          verbose)

                if not all_paths:
                    host_pair_paths[src_h_id][dst_h_id] = []
                else:
                    host_pair_paths[src_h_id][dst_h_id] = all_paths

        return host_pair_paths

    def compare_synthesis_paths(self, analyzed_path, synthesized_path, verbose):

        path_matches = True

        if len(analyzed_path) == len(synthesized_path):
            i = 0
            for path_node in analyzed_path:
                if path_node.node_id != synthesized_path[i]:
                    path_matches = False
                    break
                i += 1
        else:
            path_matches = False

        return path_matches

    def search_matching_analyzed_path(self, analyzed_host_pairs_paths, src_host, dst_host, synthesized_path, verbose):

        found_matching_path = False

        # Need to find at least one matching analyzed path
        for analyzed_path in analyzed_host_pairs_paths[src_host][dst_host]:
            found_matching_path = self.compare_synthesis_paths(analyzed_path, synthesized_path, verbose)

            if found_matching_path:
                break

        return found_matching_path

    def compare_primary_paths_with_synthesis(self, nc, analyzed_host_pairs_traffic_paths, verbose=False):

        synthesized_primary_paths = None

        if not nc.load_config and nc.save_config:
            synthesized_primary_paths = nc.synthesis.synthesis_lib.synthesized_primary_paths
        else:
            with open(nc.conf_path + "synthesized_primary_paths.json", "r") as in_file:
                synthesized_primary_paths = json.loads(in_file.read())

        all_paths_match = True

        for src_host in analyzed_host_pairs_traffic_paths:
            for dst_host in analyzed_host_pairs_traffic_paths[src_host]:

                synthesized_path = synthesized_primary_paths[src_host][dst_host]
                path_matches = self.search_matching_analyzed_path(analyzed_host_pairs_traffic_paths,
                                                                  src_host, dst_host,
                                                                  synthesized_path, verbose)
                if not path_matches:
                    print "No analyzed path matched for:", synthesized_path
                    all_paths_match = False

        return all_paths_match

    def compare_failover_paths_with_synthesis(self, nc, ng, npg, links_to_try, verbose=False):

        all_paths_match = True

        if not nc.load_config and nc.save_config:
            synthesized_primary_paths = nc.synthesis.synthesis_lib.synthesized_primary_paths
            synthesized_failover_paths = nc.synthesis.synthesis_lib.synthesized_failover_paths
        else:
            with open(nc.conf_path + "synthesized_primary_paths.json", "r") as in_file:
                synthesized_primary_paths = json.loads(in_file.read())

            with open(nc.conf_path + "synthesized_failover_paths.json", "r") as in_file:
                synthesized_failover_paths = json.loads(in_file.read())

        for link in links_to_try:

            # Ignore host links
            if link[0].startswith("h") or link[1].startswith("h"):
                continue

            print "Breaking link:", link

            npg.remove_node_graph_link(link[0], link[1])

            analyzed_host_pairs_paths = self.get_all_host_pairs_traffic_paths(ng, npg)

            for src_host in analyzed_host_pairs_paths:
                for dst_host in analyzed_host_pairs_paths[src_host]:

                    # If an link has been failed, first check both permutation of link switches, if neither is found,
                    # then refer to primary path by assuming that the given link did not participate in the failover of
                    # the given host pair.
                    try:
                        synthesized_path = synthesized_failover_paths[src_host][dst_host][link[0]][link[1]]
                    except:
                        try:
                            synthesized_path = synthesized_failover_paths[src_host][dst_host][link[1]][link[0]]
                        except:
                            synthesized_path = synthesized_primary_paths[src_host][dst_host]

                    path_matches = self.search_matching_analyzed_path(analyzed_host_pairs_paths,
                                                                      src_host, dst_host,
                                                                      synthesized_path, verbose)
                    if not path_matches:
                        print "No analyzed path matched for:", synthesized_path, "with failed link:", link
                        all_paths_match = False
                        break

            print "Restoring link:", link
            npg.add_node_graph_link(link[0], link[1], updating=True)

            if not all_paths_match:
                break

        return all_paths_match

    # def test_single_link_failure_admitted_traffic_presence_ring_aborescene_apply_true(self):
    #
    #     node_to_check = self.ng_ring_aborescene_apply_true.get_node_object("h21").switch_ingress_port
    #     dst_to_check = self.ng_ring_aborescene_apply_true.get_node_object("h31").switch_egress_port
    #     traffic_to_check = self.get_specific_traffic(self.ng_ring_aborescene_apply_true, "h21", "h31")
    #     link_to_fail = ("s1", "s4")
    #
    #     self.check_single_link_failure_admitted_traffic_subset(self.npg_ring_aborescene_apply_true,
    #                                                            node_to_check,
    #                                                            dst_to_check,
    #                                                            traffic_to_check,
    #                                                            link_to_fail)
    #
    #     node_to_check = self.ng_ring_aborescene_apply_true.get_node_object("h11").switch_ingress_port
    #     dst_to_check = self.ng_ring_aborescene_apply_true.get_node_object("h31").switch_egress_port
    #     traffic_to_check = self.get_specific_traffic(self.ng_ring_aborescene_apply_true, "h11", "h31")
    #     link_to_fail = ("s3", "s4")
    #
    #     self.check_single_link_failure_admitted_traffic_subset(self.npg_ring_aborescene_apply_true,
    #                                                            node_to_check,
    #                                                            dst_to_check,
    #                                                            traffic_to_check,
    #                                                            link_to_fail)
    #
    # def test_single_link_failure_admitted_traffic_absence_ring_aborescene_apply_true(self):
    #
    #     node_to_check = self.npg_ring_aborescene_apply_true.get_egress_node("s1", 3)
    #     dst_to_check = self.ng_ring_aborescene_apply_true.get_node_object("h31").switch_egress_port
    #     traffic_to_match = Traffic()
    #     link_to_fail = ("s1", "s4")
    #
    #     self.check_single_link_failure_admitted_traffic_match(self.npg_ring_aborescene_apply_true,
    #                                                           node_to_check,
    #                                                           dst_to_check,
    #                                                           traffic_to_match,
    #                                                           link_to_fail)
    #
    # def test_two_link_failure_admitted_traffic_absence_ring_aborescene_apply_true(self):
    #
    #     src_h_obj = self.ng_ring_aborescene_apply_true.get_node_object("h21")
    #     dst_h_obj = self.ng_ring_aborescene_apply_true.get_node_object("h31")
    #     links_to_fail = [("s1", "s4"), ("s2", "s3")]
    #
    #     self.check_two_link_failure_admitted_traffic_absence(self.npg_ring_aborescene_apply_true,
    #                                                          src_h_obj, dst_h_obj, links_to_fail)
    #
    #     src_h_obj = self.ng_ring_aborescene_apply_true.get_node_object("h21")
    #     dst_h_obj = self.ng_ring_aborescene_apply_true.get_node_object("h41")
    #     links_to_fail = [("s1", "s4"), ("s2", "s3")]
    #
    #     self.check_two_link_failure_admitted_traffic_absence(self.npg_ring_aborescene_apply_true,
    #                                                          src_h_obj, dst_h_obj, links_to_fail)
    #
    # def test_primary_paths_match_synthesized_clos_dijkstra(self):
    #     analyzed_host_pairs_traffic_paths = self.get_all_host_pairs_traffic_paths(self.ng_clos_dijkstra,
    #                                                                               self.npg_clos_dijkstra)
    #     paths_match = self.compare_primary_paths_with_synthesis(self.nc_clos_dijkstra,
    #                                                             analyzed_host_pairs_traffic_paths)
    #     self.assertEqual(paths_match, True)
    #
    # def test_failover_paths_match_synthesized_clos_dijkstra(self):
    #     paths_match = self.compare_failover_paths_with_synthesis(self.nc_clos_dijkstra,
    #                                                              self.ng_clos_dijkstra,
    #                                                              self.npg_clos_dijkstra,
    #                                                              self.ng_clos_dijkstra.graph.edges())
    #     self.assertEqual(paths_match, True)
    #

    def get_active_path(self, ng, npg, src_h_obj, dst_h_obj):

        specific_traffic = self.get_specific_traffic(ng, src_h_obj.node_id, dst_h_obj.node_id)
        at = npg.get_admitted_traffic(src_h_obj.switch_ingress_port, dst_h_obj.switch_egress_port)

        at_int = specific_traffic.intersect(at)

        paths = npg.get_paths(src_h_obj.switch_ingress_port,
                              dst_h_obj.switch_egress_port,
                              at_int,
                              [src_h_obj.switch_ingress_port],
                              [],
                              True)

        # Get the path that is currently active
        active_path = None
        for path in paths:
            if path.get_max_active_rank() == 0:
                active_path = path
                break

        return active_path

    def check_single_link_failure_causes_path_disconnect(self, ng, npg):

        # Test for every host pair
        for src_h_obj, dst_h_obj in ng.host_obj_pair_iter():

            # Test pretend-failure each link
            for ld in ng.get_switch_link_data():
                active_path = self.get_active_path(ng, npg, src_h_obj, dst_h_obj)
                fails = npg.link_failure_causes_path_disconnect(active_path, ld)
                self.assertEqual(fails, False)

    def check_two_link_failure_causes_path_disconnect(self, ng, npg):

        # First knock out one link for real
        for ld1 in ng.get_switch_link_data():

            npg.remove_node_graph_link(*ld1.forward_link)

            # Test for every host pair
            for src_h_obj, dst_h_obj in ng.host_obj_pair_iter():

                active_path_before = self.get_active_path(ng, npg, src_h_obj, dst_h_obj)

                # Test pretend-failure each link
                for ld2 in ng.get_switch_link_data():

                    # Don't fail same link twice...
                    if ld1 == ld2:
                        continue

                    active_path_after = self.get_active_path(ng,  npg, src_h_obj, dst_h_obj)

                    fails = npg.link_failure_causes_path_disconnect(active_path_after, ld2)

                    if active_path_before.passes_link(ld1):
                        if active_path_after.passes_link(ld2):
                            self.assertEqual(fails, True)

            # Restore the link for real
            npg.add_node_graph_link(*ld1.forward_link, updating=True)

    def test_single_link_failure_causes_path_disconnect_ring_aborescene_apply_true_report_active_false(self):
        self.check_single_link_failure_causes_path_disconnect(self.ng_ring_aborescene_apply_true,
                                                              self.npg_ring_aborescene_apply_true_report_active_false)

    def test_two_link_failure_causes_path_disconnect_ring_aborescene_apply_true_report_active_false(self):
        self.check_two_link_failure_causes_path_disconnect(self.ng_ring_aborescene_apply_true,
                                                           self.npg_ring_aborescene_apply_true_report_active_false)

    def test_single_link_failure_causes_path_disconnect_clos_dijkstra_report_active_false(self):
        self.check_single_link_failure_causes_path_disconnect(self.ng_clos_dijkstra,
                                                              self.npg_clos_dijkstra_report_active_false)

    def test_two_link_failure_causes_path_disconnect_clos_dijkstra_report_active_false(self):
        self.check_two_link_failure_causes_path_disconnect(self.ng_clos_dijkstra,
                                                           self.npg_clos_dijkstra_report_active_false)

if __name__ == '__main__':
    unittest.main()
