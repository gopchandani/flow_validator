import unittest
import os
import json

from model.traffic import Traffic
from model.network_port_graph import NetworkPortGraph
from experiments.network_configuration import NetworkConfiguration
from analysis.util import get_host_ports_init_egress_nodes_and_traffic
from analysis.util import get_switch_links_init_ingress_nodes_and_traffic


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

        at = None

        # Check to see if the two ports belong to the same switch

        # If they do, just the spg will do the telling, no need to consult the npg
        if src_port.sw.node_id == dst_port.sw.node_id:
            spg = src_port.sw.port_graph
            at = spg.get_admitted_traffic(src_port.switch_port_graph_ingress_node,
                                          dst_port.switch_port_graph_egress_node)

        # If they don't, then need to consult the spg of dst switch and the npg as well.
        else:
            dst_sw_spg = dst_port.sw.port_graph
            dst_sw_at_and_nodes = self.get_dst_sw_at_and_nodes(npg,
                                                               src_port.network_port_graph_ingress_node,
                                                               dst_port.sw)
            for at1, dst_sw_node in dst_sw_at_and_nodes:
                dst_sw_spg_node = dst_sw_spg.get_node(dst_sw_node.node_id)
                at2 = dst_sw_spg.get_admitted_traffic(dst_sw_spg_node, dst_port.switch_port_graph_egress_node)

                modified_at1 = at1.get_modified_traffic()
                modified_at1.set_field("in_port", int(dst_sw_node.parent_obj.port_number))

                if not at1.intersect(at2).is_empty():
                    at = at1

        return at

    def test_admitted_traffic_linear_dijkstra(self):

        h1s1 = self.ng_linear_dijkstra.get_node_object("h1s1").switch_port
        h2s1 = self.ng_linear_dijkstra.get_node_object("h2s1").switch_port
        h1s2 = self.ng_linear_dijkstra.get_node_object("h1s2").switch_port
        h2s2 = self.ng_linear_dijkstra.get_node_object("h2s2").switch_port

        # Same switch
        at = self.get_admitted_traffic(self.ng_linear_dijkstra, self.npg_linear_dijkstra, h1s1, h2s1)

        # Different switch
        at = self.get_admitted_traffic(self.ng_linear_dijkstra, self.npg_linear_dijkstra, h1s1, h1s2)


if __name__ == '__main__':
    unittest.main()
