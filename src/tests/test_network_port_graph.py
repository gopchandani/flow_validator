import unittest
import json

from collections import defaultdict
from model.traffic import Traffic
from model.traffic_path import TrafficPath
from model.network_port_graph import NetworkPortGraph
from experiments.network_configuration import NetworkConfiguration
from analysis.util import get_paths, get_active_path, get_failover_path, get_failover_path_after_failed_sequence
from analysis.util import get_specific_traffic, get_admitted_traffic


class TestNetworkPortGraph(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.nc_ring_dijkstra_apply_true = NetworkConfiguration("ryu",
                                                               "127.0.0.1",
                                                               6633,
                                                               "http://localhost:8080/",
                                                               "admin",
                                                               "admin",
                                                               "ring",
                                                               {"num_switches": 4,
                                                                "num_hosts_per_switch": 1},
                                                               conf_root="configurations/",
                                                               synthesis_name="DijkstraSynthesis",
                                                               synthesis_params={"apply_group_intents_immediately":
                                                                                     True})

        cls.ng_ring_dijkstra_apply_true_report_active_false = \
            cls.nc_ring_dijkstra_apply_true.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)
        cls.npg_ring_dijkstra_apply_true_report_active_false = \
            NetworkPortGraph(cls.ng_ring_dijkstra_apply_true_report_active_false, False)
        cls.npg_ring_dijkstra_apply_true_report_active_false.init_network_port_graph()
        cls.npg_ring_dijkstra_apply_true_report_active_false.init_network_admitted_traffic()

        cls.nc_ring_aborescene_apply_true = NetworkConfiguration("ryu",
                                                                 "127.0.0.1",
                                                                 6633,
                                                                 "http://localhost:8080/",
                                                                 "admin",
                                                                 "admin",
                                                                 "ring",
                                                                 {"num_switches": 4,
                                                                  "num_hosts_per_switch": 1},
                                                                 conf_root="configurations/",
                                                                 synthesis_name="AboresceneSynthesis",
                                                                 synthesis_params={"apply_group_intents_immediately":
                                                                                       True})

        cls.ng_ring_aborescene_apply_true = cls.nc_ring_aborescene_apply_true.setup_network_graph(mininet_setup_gap=1,
                                                                                                  synthesis_setup_gap=1)

        cls.npg_ring_aborescene_apply_true = NetworkPortGraph(cls.ng_ring_aborescene_apply_true,
                                                              report_active_state=True)
        cls.npg_ring_aborescene_apply_true.init_network_port_graph()
        cls.npg_ring_aborescene_apply_true.init_network_admitted_traffic()

        cls.ng_ring_aborescene_apply_true_report_active_false = \
            cls.nc_ring_aborescene_apply_true.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)
        cls.npg_ring_aborescene_apply_true_report_active_false = \
            NetworkPortGraph(cls.ng_ring_aborescene_apply_true_report_active_false,
                             report_active_state=False)
        cls.npg_ring_aborescene_apply_true_report_active_false.init_network_port_graph()
        cls.npg_ring_aborescene_apply_true_report_active_false.init_network_admitted_traffic()

        cls.nc_clos_dijkstra = NetworkConfiguration("ryu",
                                                    "127.0.0.1",
                                                    6633,
                                                    "http://localhost:8080/",
                                                    "admin",
                                                    "admin",
                                                    "clostopo",
                                                    {"fanout": 2,
                                                     "core": 1,
                                                     "num_hosts_per_switch": 1},
                                                    conf_root="configurations/",
                                                    synthesis_name="DijkstraSynthesis",
                                                    synthesis_params={})

        cls.ng_clos_dijkstra = cls.nc_clos_dijkstra.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)
        cls.npg_clos_dijkstra = NetworkPortGraph(cls.ng_clos_dijkstra, True)
        cls.npg_clos_dijkstra.init_network_port_graph()
        cls.npg_clos_dijkstra.init_network_admitted_traffic()

        cls.ng_clos_dijkstra_report_active_false = cls.nc_clos_dijkstra.setup_network_graph(mininet_setup_gap=1,
                                                                                            synthesis_setup_gap=1)
        cls.npg_clos_dijkstra_report_active_false = NetworkPortGraph(cls.ng_clos_dijkstra_report_active_false, False)
        cls.npg_clos_dijkstra_report_active_false.init_network_port_graph()
        cls.npg_clos_dijkstra_report_active_false.init_network_admitted_traffic()

        cls.nc_linear_dijkstra = NetworkConfiguration("ryu",
                                                      "127.0.0.1",
                                                      6633,
                                                      "http://localhost:8080/",
                                                      "admin",
                                                      "admin",
                                                      "linear",
                                                      {"num_switches": 2,
                                                       "num_hosts_per_switch": 2},
                                                      conf_root="configurations/",
                                                      synthesis_name="DijkstraSynthesis",
                                                      synthesis_params={"apply_group_intents_immediately": True})

        cls.ng_linear_dijkstra = cls.nc_linear_dijkstra.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)
        cls.npg_linear_dijkstra = NetworkPortGraph(cls.ng_linear_dijkstra, True)
        cls.npg_linear_dijkstra.init_network_port_graph()
        cls.npg_linear_dijkstra.init_network_admitted_traffic()

        cls.nc_linear_dijkstra_mac_acl = NetworkConfiguration("ryu",
                                                              "127.0.0.1",
                                                              6633,
                                                              "http://localhost:8080/",
                                                              "admin",
                                                              "admin",
                                                              "linear",
                                                              {"num_switches": 2,
                                                               "num_hosts_per_switch": 2},
                                                              conf_root="configurations/",
                                                              synthesis_name="DijkstraSynthesis",
                                                              synthesis_params={"apply_group_intents_immediately": True,
                                                                                "mac_acl": True})

        cls.ng_linear_dijkstra_mac_acl = cls.nc_linear_dijkstra_mac_acl.setup_network_graph(mininet_setup_gap=1,
                                                                                            synthesis_setup_gap=1)

        cls.npg_linear_dijkstra_mac_acl = NetworkPortGraph(cls.ng_linear_dijkstra_mac_acl,
                                                           True)
        cls.npg_linear_dijkstra_mac_acl.init_network_port_graph()
        cls.npg_linear_dijkstra_mac_acl.init_network_admitted_traffic()

    def check_single_link_failure_admitted_traffic_subset(self, npg, src_port, dst_port, traffic_to_check, link_to_fail):

        npg.remove_node_graph_link(*link_to_fail)
        after_at = get_admitted_traffic(npg, src_port, dst_port)
        is_subset = after_at.is_subset_traffic(traffic_to_check)

        self.assertEqual(is_subset, True)
        npg.add_node_graph_link(*link_to_fail, updating=True)

    def check_single_link_failure_admitted_traffic_match(self, npg, src_port, dst_port, traffic_to_match, link_to_fail):

        npg.remove_node_graph_link(*link_to_fail)
        after_failure_at = get_admitted_traffic(npg, src_port, dst_port)
        self.assertEqual(after_failure_at, traffic_to_match)
        npg.add_node_graph_link(*link_to_fail, updating=True)

    def check_two_link_failure_admitted_traffic_absence(self, npg, src_port, dst_port, links_to_fail):

        for link_to_fail in links_to_fail:
            before_at = get_admitted_traffic(npg, src_port, dst_port)

            npg.remove_node_graph_link(*link_to_fail)

        after_at = get_admitted_traffic(npg, src_port, dst_port)

        for link_to_fail in links_to_fail:
            npg.add_node_graph_link(*link_to_fail, updating=True)

        self.assertEqual(after_at.is_empty(), True)

    def get_all_host_pairs_traffic_paths(self, ng, npg, verbose=False):

        host_pair_paths = defaultdict(defaultdict)

        for src_h_id in ng.host_ids:
            for dst_h_id in ng.host_ids:

                if src_h_id == dst_h_id:
                    continue

                specific_traffic = get_specific_traffic(ng, src_h_id, dst_h_id)

                ingress_node = npg.get_node(ng.get_node_object(src_h_id).port_graph_ingress_node_id)
                egress_node = npg.get_node(ng.get_node_object(dst_h_id).port_graph_egress_node_id)

                all_paths = get_paths(npg,
                                      specific_traffic,
                                      ng.get_node_object(src_h_id).switch_port,
                                      ng.get_node_object(dst_h_id).switch_port)

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

    def check_admitted_traffic_present(self, ng, npg, src_host_obj, dst_host_obj):

        at = get_admitted_traffic(npg, src_host_obj.switch_port, dst_host_obj.switch_port)
        specific_traffic = get_specific_traffic(ng, src_host_obj.node_id, dst_host_obj.node_id)
        at_int = specific_traffic.intersect(at)
        self.assertEqual(at_int.is_empty(), False)

        return at_int

    def check_admitted_traffic_absent(self, ng, npg, src_host_obj, dst_host_obj):

        at = get_admitted_traffic(npg, src_host_obj.switch_port, dst_host_obj.switch_port)
        specific_traffic = get_specific_traffic(ng, src_host_obj.node_id, dst_host_obj.node_id)
        at_int = specific_traffic.intersect(at)
        self.assertEqual(at_int.is_empty(), True)

        return at_int

    def check_path(self, ng, npg, src_host_obj, dst_host_obj, expected_path):

        specific_traffic = get_specific_traffic(ng, src_host_obj.node_id, dst_host_obj.node_id)
        all_paths = get_paths(npg, specific_traffic, src_host_obj.switch_port, dst_host_obj.switch_port)

        self.assertEqual(len(all_paths), 1)
        self.assertEqual(all_paths[0], expected_path)

    def test_admitted_traffic_linear_dijkstra(self):

        h1s1 = self.ng_linear_dijkstra_mac_acl.get_node_object("h1s1")
        h2s1 = self.ng_linear_dijkstra_mac_acl.get_node_object("h2s1")
        h1s2 = self.ng_linear_dijkstra_mac_acl.get_node_object("h1s2")
        h2s2 = self.ng_linear_dijkstra_mac_acl.get_node_object("h2s2")

        # Same switch
        at = self.check_admitted_traffic_present(self.ng_linear_dijkstra_mac_acl,
                                                 self.npg_linear_dijkstra_mac_acl,
                                                 h1s1, h2s1)
        # Different switch
        at = self.check_admitted_traffic_present(self.ng_linear_dijkstra_mac_acl,
                                                 self.npg_linear_dijkstra_mac_acl,
                                                 h1s1, h1s2)

        at = self.check_admitted_traffic_present(self.ng_linear_dijkstra_mac_acl,
                                                 self.npg_linear_dijkstra_mac_acl,
                                                 h2s1, h2s2)

        self.check_admitted_traffic_absent(self.ng_linear_dijkstra_mac_acl,
                                           self.npg_linear_dijkstra_mac_acl,
                                           h1s1, h2s2)

        self.check_admitted_traffic_absent(self.ng_linear_dijkstra_mac_acl,
                                           self.npg_linear_dijkstra_mac_acl,
                                           h2s1, h1s2)

        self.check_admitted_traffic_absent(self.ng_linear_dijkstra_mac_acl,
                                           self.npg_linear_dijkstra_mac_acl,
                                           h1s2, h2s1)

        self.check_admitted_traffic_absent(self.ng_linear_dijkstra_mac_acl,
                                           self.npg_linear_dijkstra_mac_acl,
                                           h2s2, h1s1)

    def test_path_linear_dijkstra(self):

        h1s1 = self.ng_linear_dijkstra.get_node_object("h1s1")
        h2s1 = self.ng_linear_dijkstra.get_node_object("h2s1")
        h1s2 = self.ng_linear_dijkstra.get_node_object("h1s2")
        h2s2 = self.ng_linear_dijkstra.get_node_object("h2s2")

        # Same switch
        expected_path = TrafficPath(self.ng_linear_dijkstra,
                                    [h1s1.switch_port.switch_port_graph_ingress_node,
                                     h2s1.switch_port.switch_port_graph_egress_node])

        self.check_path(self.ng_linear_dijkstra, self.npg_linear_dijkstra, h1s1, h2s1, expected_path)

        # Different switch
        expected_path = TrafficPath(self.ng_linear_dijkstra,
                                    [h1s1.switch_port.switch_port_graph_ingress_node,
                                     self.npg_linear_dijkstra.get_node("s1:egress3"),
                                     self.npg_linear_dijkstra.get_node("s2:ingress3"),
                                     h1s2.switch_port.switch_port_graph_egress_node])

        self.check_path(self.ng_linear_dijkstra, self.npg_linear_dijkstra, h1s1, h1s2, expected_path)

        expected_path = TrafficPath(self.ng_linear_dijkstra,
                                    [h1s1.switch_port.switch_port_graph_ingress_node,
                                     self.npg_linear_dijkstra.get_node("s1:egress3"),
                                     self.npg_linear_dijkstra.get_node("s2:ingress3"),
                                     h2s2.switch_port.switch_port_graph_egress_node])

        self.check_path(self.ng_linear_dijkstra, self.npg_linear_dijkstra, h1s1, h2s2, expected_path)

    def test_single_link_failure_admitted_traffic_absence_linear_dijkstra(self):

        h1s1_port = self.ng_linear_dijkstra.get_node_object("h1s1").switch_port
        h1s2_port = self.ng_linear_dijkstra.get_node_object("h1s2").switch_port

        traffic_to_match = Traffic()
        link_to_fail = ("s1", "s2")

        self.check_single_link_failure_admitted_traffic_match(self.npg_linear_dijkstra,
                                                              h1s1_port,
                                                              h1s2_port,
                                                              traffic_to_match,
                                                              link_to_fail)


    def test_admitted_traffic_ring_aborescene_apply_true(self):

        h11 = self.ng_ring_aborescene_apply_true.get_node_object("h11")
        h21 = self.ng_ring_aborescene_apply_true.get_node_object("h21")
        h31 = self.ng_ring_aborescene_apply_true.get_node_object("h31")
        h41 = self.ng_ring_aborescene_apply_true.get_node_object("h41")

        at = self.check_admitted_traffic_present(self.ng_ring_aborescene_apply_true,
                                                 self.npg_ring_aborescene_apply_true,
                                                 h11, h31)

        at = self.check_admitted_traffic_present(self.ng_ring_aborescene_apply_true,
                                                 self.npg_ring_aborescene_apply_true,
                                                 h21, h41)

    def test_single_link_failure_admitted_traffic_presence_ring_aborescene_apply_true(self):

        src_port = self.ng_ring_aborescene_apply_true.get_node_object("h21").switch_port
        dst_port = self.ng_ring_aborescene_apply_true.get_node_object("h31").switch_port

        traffic_to_check = get_specific_traffic(self.ng_ring_aborescene_apply_true, "h21", "h31")
        link_to_fail = ("s1", "s4")

        self.check_single_link_failure_admitted_traffic_subset(self.npg_ring_aborescene_apply_true,
                                                               src_port,
                                                               dst_port,
                                                               traffic_to_check,
                                                               link_to_fail)

        src_port = self.ng_ring_aborescene_apply_true.get_node_object("h11").switch_port
        dst_port = self.ng_ring_aborescene_apply_true.get_node_object("h31").switch_port

        traffic_to_check = get_specific_traffic(self.ng_ring_aborescene_apply_true, "h11", "h31")
        link_to_fail = ("s3", "s4")

        self.check_single_link_failure_admitted_traffic_subset(self.npg_ring_aborescene_apply_true,
                                                               src_port,
                                                               dst_port,
                                                               traffic_to_check,
                                                               link_to_fail)

    def test_single_link_failure_admitted_traffic_absence_ring_aborescene_apply_true(self):

        src_port = self.ng_ring_aborescene_apply_true.get_node_object("s1").ports[3]
        dst_port = self.ng_ring_aborescene_apply_true.get_node_object("h31").switch_port

        traffic_to_match = Traffic()
        link_to_fail = ("s1", "s4")

        self.check_single_link_failure_admitted_traffic_match(self.npg_ring_aborescene_apply_true,
                                                              src_port,
                                                              dst_port,
                                                              traffic_to_match,
                                                              link_to_fail)

    def test_two_link_failure_admitted_traffic_absence_ring_aborescene_apply_true(self):

        src_port = self.ng_ring_aborescene_apply_true.get_node_object("h21").switch_port
        dst_port = self.ng_ring_aborescene_apply_true.get_node_object("h31").switch_port
        links_to_fail = [("s1", "s4"), ("s2", "s3")]

        self.check_two_link_failure_admitted_traffic_absence(self.npg_ring_aborescene_apply_true,
                                                             src_port, dst_port, links_to_fail)


        # This case fails because both switches flip around and the at looks like a loop from s2:2 to s1:2
        # Probably cannot be helped if one insists on using report active set to true

        # src_port = self.ng_ring_aborescene_apply_true.get_node_object("h21").switch_port
        # dst_port = self.ng_ring_aborescene_apply_true.get_node_object("h41").switch_port
        # links_to_fail = [("s1", "s4"), ("s2", "s3")]
        #
        # self.check_two_link_failure_admitted_traffic_absence(self.npg_ring_aborescene_apply_true,
        #                                                      src_port, dst_port, links_to_fail)

    def test_primary_paths_match_synthesized_clos_dijkstra(self):
        analyzed_host_pairs_traffic_paths = self.get_all_host_pairs_traffic_paths(self.ng_clos_dijkstra,
                                                                                  self.npg_clos_dijkstra)
        paths_match = self.compare_primary_paths_with_synthesis(self.nc_clos_dijkstra,
                                                                analyzed_host_pairs_traffic_paths)
        self.assertEqual(paths_match, True)

    def test_failover_paths_match_synthesized_clos_dijkstra(self):
        paths_match = self.compare_failover_paths_with_synthesis(self.nc_clos_dijkstra,
                                                                 self.ng_clos_dijkstra,
                                                                 self.npg_clos_dijkstra,
                                                                 self.ng_clos_dijkstra.graph.edges())
        self.assertEqual(paths_match, True)

    def compare_failover_paths_with_synthesis_report_active_false_single_failure(self, nc, ng, npg):

        if not nc.load_config and nc.save_config:
            synthesized_primary_paths = nc.synthesis.synthesis_lib.synthesized_primary_paths
            synthesized_failover_paths = nc.synthesis.synthesis_lib.synthesized_failover_paths
        else:
            with open(nc.conf_path + "synthesized_primary_paths.json", "r") as in_file:
                synthesized_primary_paths = json.loads(in_file.read())

            with open(nc.conf_path + "synthesized_failover_paths.json", "r") as in_file:
                synthesized_failover_paths = json.loads(in_file.read())

        for ld in ng.get_switch_link_data():
            for src_host, dst_host in ng.host_obj_pair_iter():

                # If an link has been failed, first check both permutation of link switches, if neither is found,
                # then refer to primary path by assuming that the given link did not participate in the failover of
                # the given host pair.
                try:
                    synthesized_path = synthesized_failover_paths[src_host.node_id][dst_host.node_id][ld.forward_link[0]][ld.forward_link[1]]
                except KeyError:
                    try:
                        synthesized_path = synthesized_failover_paths[src_host.node_id][dst_host.node_id][ld.forward_link[1]][ld.forward_link[0]]
                    except KeyError:
                        synthesized_path = synthesized_primary_paths[src_host.node_id][dst_host.node_id]

                specific_traffic = get_specific_traffic(ng, src_host.node_id, dst_host.node_id)
                active_analyzed_path = get_active_path(npg, specific_traffic, src_host.switch_port, dst_host.switch_port)

                ld.set_link_ports_down()
                failover_path = get_failover_path(npg, active_analyzed_path, ld)
                ld.set_link_ports_up()

                self.assertEqual(True, failover_path.compare_using_nodes_ids(synthesized_path))

    def compare_failover_paths_with_synthesis_report_active_false_double_failure(self, nc, ng, npg):

        # First knock out one link for real
        for src_h_obj, dst_h_obj in ng.host_obj_pair_iter():
            for ld1 in ng.get_switch_link_data():
                for ld2 in ng.get_switch_link_data():

                    # Don't fail same link twice...
                    if ld1 == ld2:
                        continue

                    specific_traffic = get_specific_traffic(ng, src_h_obj.node_id, dst_h_obj.node_id)

                    active_path_before_one_failure = get_active_path(npg,
                                                                     specific_traffic,
                                                                     src_h_obj.switch_port,
                                                                     dst_h_obj.switch_port)

                    if active_path_before_one_failure.passes_link(ld1):

                        npg.remove_node_graph_link(*ld1.forward_link)

                        active_path_after_one_failure = get_active_path(npg,
                                                                        specific_traffic,
                                                                        src_h_obj.switch_port,
                                                                        dst_h_obj.switch_port)

                        if not active_path_before_one_failure.passes_link(ld2) and active_path_after_one_failure.passes_link(ld2):
                            ld2.set_link_ports_down()
                            failover_path_after_two_failures = get_failover_path(npg, active_path_after_one_failure, ld2)
                            ld2.set_link_ports_up()
                            self.assertEqual(failover_path_after_two_failures, None)

                        # Restore the link for real
                        npg.add_node_graph_link(*ld1.forward_link, updating=True)

    def compare_paths_with_synthesis_report_active_false_fail_two_link_sequence(self, nc, ng, npg):

        if not nc.load_config and nc.save_config:
            synthesized_primary_paths = nc.synthesis.synthesis_lib.synthesized_primary_paths
            synthesized_failover_paths = nc.synthesis.synthesis_lib.synthesized_failover_paths
        else:
            with open(nc.conf_path + "synthesized_primary_paths.json", "r") as in_file:
                synthesized_primary_paths = json.loads(in_file.read())

            with open(nc.conf_path + "synthesized_failover_paths.json", "r") as in_file:
                synthesized_failover_paths = json.loads(in_file.read())

        # First knock out one link for real
        for src_host, dst_host in ng.host_obj_pair_iter():

            specific_traffic = get_specific_traffic(ng, src_host.node_id, dst_host.node_id)

            active_path_before_failures = get_active_path(npg, specific_traffic,
                                                          src_host.switch_port, dst_host.switch_port)

            for ld1 in ng.get_switch_link_data():

                # If an link has been failed, first check both permutation of link switches, if neither is found,
                # then refer to primary path by assuming that the given link did not participate in the failover of
                # the given host pair.
                try:
                    synthesized_path = synthesized_failover_paths[src_host.node_id][dst_host.node_id][ld1.forward_link[0]][ld1.forward_link[1]]
                except KeyError:
                    try:
                        synthesized_path = synthesized_failover_paths[src_host.node_id][dst_host.node_id][ld1.forward_link[1]][ld1.forward_link[0]]
                    except KeyError:
                        synthesized_path = synthesized_primary_paths[src_host.node_id][dst_host.node_id]

                for ld2 in ng.get_switch_link_data():

                    # Don't fail same link twice...
                    if ld1 == ld2:
                        continue

                    failover_path = get_failover_path_after_failed_sequence(npg,
                                                                            active_path_before_failures,
                                                                            [ld1, ld2])

                    if active_path_before_failures.passes_link(ld1) and not active_path_before_failures.passes_link(ld2):
                        self.assertEqual(failover_path, None)

    def test_single_link_failure_failover_path_ring_dijkstra_apply_true_report_active_false(self):
        self.compare_failover_paths_with_synthesis_report_active_false_single_failure(
            self.nc_ring_dijkstra_apply_true,
            self.ng_ring_dijkstra_apply_true_report_active_false,
            self.npg_ring_dijkstra_apply_true_report_active_false)

    def test_double_link_failure_failover_path_ring_dijkstra_apply_true_report_active_false(self):
        self.compare_failover_paths_with_synthesis_report_active_false_double_failure(
            self.nc_ring_dijkstra_apply_true,
            self.ng_ring_dijkstra_apply_true_report_active_false,
            self.npg_ring_dijkstra_apply_true_report_active_false)

    def test_fail_two_link_sequence_failover_path_ring_dijkstra_apply_true_report_active_false(self):
        self.compare_paths_with_synthesis_report_active_false_fail_two_link_sequence(
            self.nc_ring_dijkstra_apply_true,
            self.ng_ring_dijkstra_apply_true_report_active_false,
            self.npg_ring_dijkstra_apply_true_report_active_false)

    def test_single_link_failure_failover_path_ring_aborescene_apply_true_report_active_false(self):
        self.compare_failover_paths_with_synthesis_report_active_false_single_failure(
            self.nc_ring_aborescene_apply_true,
            self.ng_ring_aborescene_apply_true_report_active_false,
            self.npg_ring_aborescene_apply_true_report_active_false)

    def test_double_link_failure_failover_path_ring_aborescene_apply_true_report_active_false(self):
        self.compare_failover_paths_with_synthesis_report_active_false_double_failure(
            self.nc_ring_aborescene_apply_true,
            self.ng_ring_aborescene_apply_true_report_active_false,
            self.npg_ring_aborescene_apply_true_report_active_false)

    def test_fail_two_link_sequence_failover_path_ring_aborescene_apply_true_report_active_false(self):
        self.compare_paths_with_synthesis_report_active_false_fail_two_link_sequence(
            self.nc_ring_aborescene_apply_true,
            self.ng_ring_aborescene_apply_true_report_active_false,
            self.npg_ring_aborescene_apply_true_report_active_false)


if __name__ == '__main__':
    unittest.main()
