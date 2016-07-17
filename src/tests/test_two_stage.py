import unittest

from model.traffic_path import TrafficPath
from model.network_port_graph import NetworkPortGraph
from experiments.network_configuration import NetworkConfiguration
from analysis.util import get_switch_links_init_ingress_nodes_and_traffic, get_specific_traffic
from analysis.util import get_admitted_traffic, get_paths


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

    def test_admitted_traffic_linear_dijkstra(self):

        h1s1 = self.ng_linear_dijkstra.get_node_object("h1s1").switch_port
        h2s1 = self.ng_linear_dijkstra.get_node_object("h2s1").switch_port
        h1s2 = self.ng_linear_dijkstra.get_node_object("h1s2").switch_port
        h2s2 = self.ng_linear_dijkstra.get_node_object("h2s2").switch_port

        # Same switch
        at1 = get_admitted_traffic(self.ng_linear_dijkstra, self.npg_linear_dijkstra, h1s1, h2s1)
        specific_traffic = get_specific_traffic(self.ng_linear_dijkstra, "h1s1", "h2s1")
        at_int = specific_traffic.intersect(at1)
        self.assertNotEqual(at_int.is_empty(), True)

        # Different switch
        at2 = get_admitted_traffic(self.ng_linear_dijkstra, self.npg_linear_dijkstra, h1s1, h1s2)
        specific_traffic = get_specific_traffic(self.ng_linear_dijkstra, "h1s1", "h1s2")
        at_int = specific_traffic.intersect(at2)
        self.assertNotEqual(at_int.is_empty(), True)

        at3 = get_admitted_traffic(self.ng_linear_dijkstra, self.npg_linear_dijkstra, h1s1, h2s2)
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
        all_paths = get_paths(self.ng_linear_dijkstra, self.npg_linear_dijkstra, specific_traffic, h1s1, h2s1)

        expected_path = TrafficPath(self.ng_linear_dijkstra,
                                    [self.npg_linear_dijkstra.get_node("s1:ingress1"),
                                     self.npg_linear_dijkstra.get_node("s1:egress2")])

        self.assertEqual(len(all_paths), 1)
        self.assertEqual(all_paths[0], expected_path)

        # Different switch
        specific_traffic = get_specific_traffic(self.ng_linear_dijkstra, "h1s1", "h1s2")
        all_paths = get_paths(self.ng_linear_dijkstra, self.npg_linear_dijkstra, specific_traffic, h1s1, h1s2)

        expected_path = TrafficPath(self.ng_linear_dijkstra,
                                    [self.npg_linear_dijkstra.get_node("s1:ingress1"),
                                     self.npg_linear_dijkstra.get_node("s1:egress3"),
                                     self.npg_linear_dijkstra.get_node("s2:ingress3"),
                                     self.npg_linear_dijkstra.get_node("s2:egress1")])

        self.assertEqual(len(all_paths), 1)
        self.assertEqual(all_paths[0], expected_path)

        specific_traffic = get_specific_traffic(self.ng_linear_dijkstra, "h1s1", "h2s2")
        all_paths = get_paths(self.ng_linear_dijkstra, self.npg_linear_dijkstra, specific_traffic, h1s1, h2s2)

        expected_path = TrafficPath(self.ng_linear_dijkstra,
                                    [self.npg_linear_dijkstra.get_node("s1:ingress1"),
                                     self.npg_linear_dijkstra.get_node("s1:egress3"),
                                     self.npg_linear_dijkstra.get_node("s2:ingress3"),
                                     self.npg_linear_dijkstra.get_node("s2:egress2")])

        self.assertEqual(len(all_paths), 1)
        self.assertEqual(all_paths[0], expected_path)


if __name__ == '__main__':
    unittest.main()
