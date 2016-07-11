import unittest
import os
import json

from collections import defaultdict
from model.traffic import Traffic
from model.network_port_graph import NetworkPortGraph
from experiments.network_configuration import NetworkConfiguration


class TestNetworkPortGraph(unittest.TestCase):

    def test_two_stage(self):

        nc_linear_dijkstra = NetworkConfiguration("ryu",
                                                  "linear",
                                                  {"num_switches": 2,
                                                   "num_hosts_per_switch": 1},
                                                  conf_root="configurations/",
                                                  synthesis_name="DijkstraSynthesis",
                                                  synthesis_params={"apply_group_intents_immediately": True})

        ng_linear_dijkstra = nc_linear_dijkstra.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

        npg_linear_dijkstra = NetworkPortGraph(ng_linear_dijkstra, True)
        npg_linear_dijkstra.init_network_port_graph()

if __name__ == '__main__':
    unittest.main()
