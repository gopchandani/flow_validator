import unittest
import os
import json

from model.traffic import Traffic
from model.traffic_path import TrafficPath
from model.network_port_graph import NetworkPortGraph
from experiments.network_configuration import NetworkConfiguration
from analysis.util import get_host_ports_init_egress_nodes_and_traffic
from analysis.util import get_switch_links_init_ingress_nodes_and_traffic, get_specific_traffic


class TestNetworkPortGraph(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.nc_linear_dijkstra = NetworkConfiguration("ryu",
                                                      "linear",
                                                      {"num_switches": 2,
                                                       "num_hosts_per_switch": 2},
                                                      conf_root="configurations/",
                                                      synthesis_name="DijkstraSynthesis",
                                                      synthesis_params={"apply_group_intents_immediately": True})

        cls.ng_linear_dijkstra = cls.nc_linear_dijkstra.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

        cls.npg_linear_dijkstra = NetworkPortGraph(cls.ng_linear_dijkstra, True)
        cls.npg_linear_dijkstra.init_network_port_graph()

        # host_egress_nodes, init_admitted_traffic = \
        #     get_host_ports_init_egress_nodes_and_traffic(cls.ng_linear_dijkstra,
        #                                                  cls.npg_linear_dijkstra)

        link_egress_nodes, init_admitted_traffic = \
            get_switch_links_init_ingress_nodes_and_traffic(cls.ng_linear_dijkstra,
                                                            cls.npg_linear_dijkstra)

        cls.npg_linear_dijkstra.init_network_admitted_traffic(link_egress_nodes,
                                                              init_admitted_traffic)

    def get_dst_sw_at_and_nodes(self, npg, node, dst_sw):

        dst_sw_at_and_nodes = []
        for dst_node in node.admitted_traffic:
            if dst_node.sw == dst_sw:
                at = npg.get_admitted_traffic(node, dst_node)
                dst_sw_at_and_nodes.append((at, dst_node))

        return dst_sw_at_and_nodes

    def get_admitted_traffic(self, ng, npg, src_port, dst_port):

        at = Traffic()

        # Check to see if the two ports belong to the same switch

        # If they do, just the spg will do the telling, no need to use the npg
        if src_port.sw.node_id == dst_port.sw.node_id:
            spg = src_port.sw.port_graph
            at = spg.get_admitted_traffic(src_port.switch_port_graph_ingress_node,
                                          dst_port.switch_port_graph_egress_node)

        # If they don't, then need to use the spg of dst switch and the npg as well.
        else:
            dst_sw_spg = dst_port.sw.port_graph
            dst_sw_at_and_nodes = self.get_dst_sw_at_and_nodes(npg,
                                                               src_port.network_port_graph_ingress_node,
                                                               dst_port.sw)
            for at_ng, dst_sw_node in dst_sw_at_and_nodes:
                dst_sw_spg_node = dst_sw_spg.get_node(dst_sw_node.node_id)
                at_dst_spg = dst_sw_spg.get_admitted_traffic(dst_sw_spg_node, dst_port.switch_port_graph_egress_node)

                modified_at_ng = at_ng.get_modified_traffic()
                modified_at_ng.set_field("in_port", int(dst_sw_node.parent_obj.port_number))

                i = at_dst_spg.intersect(modified_at_ng)

                if not i.is_empty():
                    i.set_field("in_port", int(src_port.port_number))
                    at.union(i.get_orig_traffic(use_embedded_switch_modifications=True))

        return at

    def get_paths(self, ng, npg, specific_traffic, src_port, dst_port):

        traffic_paths = []

        # Check to see if the two ports belong to the same switch
        at = self.get_admitted_traffic(ng, npg, src_port, dst_port)

        # See if the at carries traffic
        at_int = specific_traffic.intersect(at)

        # If the intersection is empty, then no paths exist, but if not...
        if not at_int.is_empty():

            # If the ports belong to the same switch, path always has two nodes from the npg
            if src_port.sw.node_id == dst_port.sw.node_id:

                path = TrafficPath(npg, [npg.get_node(src_port.switch_port_graph_ingress_node.node_id),
                                         npg.get_node(dst_port.switch_port_graph_egress_node.node_id)])
                traffic_paths.append(path)

            # If they don't, then need to use the spg of dst switch and the npg as well.
            else:
                dst_sw_at_and_nodes = self.get_dst_sw_at_and_nodes(npg,
                                                                   src_port.network_port_graph_ingress_node,
                                                                   dst_port.sw)
                for at_ng, dst_sw_node in dst_sw_at_and_nodes:

                    # First get the paths to node(s) at dst_sw.
                    traffic_paths.extend(npg.get_paths(src_port.network_port_graph_ingress_node,
                                                       dst_sw_node,
                                                       at_int,
                                                       [src_port.network_port_graph_ingress_node],
                                                       [],
                                                       False))

                # Then add the last node in the paths
                for path in traffic_paths:
                    path.path_nodes.append(dst_port.network_port_graph_egress_node)

        return traffic_paths

    def test_admitted_traffic_linear_dijkstra(self):

        h1s1 = self.ng_linear_dijkstra.get_node_object("h1s1").switch_port
        h2s1 = self.ng_linear_dijkstra.get_node_object("h2s1").switch_port
        h1s2 = self.ng_linear_dijkstra.get_node_object("h1s2").switch_port
        h2s2 = self.ng_linear_dijkstra.get_node_object("h2s2").switch_port

        # Same switch
        at1 = self.get_admitted_traffic(self.ng_linear_dijkstra, self.npg_linear_dijkstra, h1s1, h2s1)
        specific_traffic = get_specific_traffic(self.ng_linear_dijkstra, "h1s1", "h2s1")
        at_int = specific_traffic.intersect(at1)
        self.assertNotEqual(at_int.is_empty(), True)

        # Different switch
        at2 = self.get_admitted_traffic(self.ng_linear_dijkstra, self.npg_linear_dijkstra, h1s1, h1s2)
        specific_traffic = get_specific_traffic(self.ng_linear_dijkstra, "h1s1", "h1s2")
        at_int = specific_traffic.intersect(at2)
        self.assertNotEqual(at_int.is_empty(), True)

        at3 = self.get_admitted_traffic(self.ng_linear_dijkstra, self.npg_linear_dijkstra, h1s1, h2s2)
        specific_traffic = get_specific_traffic(self.ng_linear_dijkstra, "h1s1", "h2s2")
        at_int = specific_traffic.intersect(at3)
        self.assertNotEqual(at_int.is_empty(), True)

    def test_paths_linear_dijkstra(self):
        h1s1 = self.ng_linear_dijkstra.get_node_object("h1s1").switch_port
        h2s1 = self.ng_linear_dijkstra.get_node_object("h2s1").switch_port
        h1s2 = self.ng_linear_dijkstra.get_node_object("h1s2").switch_port
        h2s2 = self.ng_linear_dijkstra.get_node_object("h2s2").switch_port

        # Same switch
        specific_traffic = get_specific_traffic(self.ng_linear_dijkstra, "h1s1", "h2s1")
        all_paths = self.get_paths(self.ng_linear_dijkstra, self.npg_linear_dijkstra, specific_traffic, h1s1, h2s1)

        expected_path = TrafficPath(self.ng_linear_dijkstra,
                                    [self.npg_linear_dijkstra.get_node("s1:ingress1"),
                                     self.npg_linear_dijkstra.get_node("s1:egress2")])

        self.assertEqual(len(all_paths), 1)
        self.assertEqual(all_paths[0], expected_path)

        # Different switch
        specific_traffic = get_specific_traffic(self.ng_linear_dijkstra, "h1s1", "h1s2")
        all_paths = self.get_paths(self.ng_linear_dijkstra, self.npg_linear_dijkstra, specific_traffic, h1s1, h1s2)

        expected_path = TrafficPath(self.ng_linear_dijkstra,
                                    [self.npg_linear_dijkstra.get_node("s1:ingress1"),
                                     self.npg_linear_dijkstra.get_node("s1:egress3"),
                                     self.npg_linear_dijkstra.get_node("s2:ingress3"),
                                     self.npg_linear_dijkstra.get_node("s2:egress1")])

        self.assertEqual(len(all_paths), 1)
        self.assertEqual(all_paths[0], expected_path)


if __name__ == '__main__':
    unittest.main()
