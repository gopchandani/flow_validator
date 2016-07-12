import unittest
import os
import json

from model.network_port_graph import NetworkPortGraph
from experiments.network_configuration import NetworkConfiguration
from analysis.util import get_host_ports_init_egress_nodes_and_traffic
from analysis.util import get_switch_links_init_egress_nodes_and_traffic


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
            get_switch_links_init_egress_nodes_and_traffic(cls.ng_linear_dijkstra,
                                                           cls.npg_linear_dijkstra)

        cls.npg_linear_dijkstra.init_network_admitted_traffic(link_egress_nodes,
                                                              init_admitted_traffic)

    def test_two_stage(self):
        print "here"

if __name__ == '__main__':
    unittest.main()
