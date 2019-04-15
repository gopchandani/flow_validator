__author__ = 'Rakesh Kumar'

from mininet.topo import Topo
import networkx as nx
import random
import math
from networkx import is_biconnected


class AdHocTopo(Topo):

    def __init__(self, params):
        Topo.__init__(self)
        self.params = params
        self.graph = nx.Graph()
        random.seed(self.params["seed"])

        self.total_switches = self.params["num_switches"]
        self.switch_names = []
        self.prepare_adhoc_topology()
        self.init_mininet_topo()

    def dist(self, sw1_dict, sw2_dict):
        x_diff = sw2_dict["x_pos"] - sw1_dict["x_pos"]
        y_diff = sw2_dict["y_pos"] - sw1_dict["y_pos"]
        return math.sqrt(x_diff**2 + y_diff ** 2)

    def add_edges_within_threshold(self, thresh):
        for sw_id_1 in self.graph.nodes():
            for sw_id_2 in self.graph.nodes():
                if sw_id_1 == sw_id_2:
                    continue

                s1 = self.graph.node[sw_id_1]["s"]
                s2 = self.graph.node[sw_id_2]["s"]

                #print s1["switch_id"], s2["switch_id"], self.dist(s1, s2), thresh

                if self.dist(s1, s2) < thresh:
                    self.graph.add_edge(sw_id_1, sw_id_2)
                    #print "Adding edge:", (sw_id_1, sw_id_2)

    def prepare_adhoc_topology(self):

        # Initialize switches and their locations
        for i in xrange(self.total_switches):
            switch_id = "s" + str(i+1)
            s_dict = {"switch_id": switch_id,
                      "x_pos": random.uniform(self.params["min_x"], self.params["max_x"]),
                      "y_pos": random.uniform(self.params["min_y"], self.params["max_y"])
                      }
            self.graph.add_node(switch_id, s=s_dict)

        # Add edges if the distance between switches is within a threshold
        max_dist = math.sqrt(
            (self.params["max_x"] - self.params["min_x"]) ** 2 + (self.params["max_y"] - self.params["min_y"]) ** 2)

        for thresh_frac in [x/1000.0 for x in xrange(1, 1000)]:
            thresh = thresh_frac * max_dist
            self.add_edges_within_threshold(thresh)
            if is_biconnected(self.graph):
                print thresh_frac
                break

    def init_mininet_topo(self):
        #  Add switches and hosts under them
        for i, sw_id in enumerate(self.graph.nodes()):
            curr_switch = self.addSwitch(sw_id, protocols="OpenFlow14")
            self.switch_names.append(curr_switch)

            for j in xrange(self.params["num_hosts_per_switch"]):
                curr_switch_host = self.addHost("h" + str(i+1) + str(j+1))
                self.addLink(curr_switch, curr_switch_host)

        #  Add links between switches
        for e in self.graph.edges():
            self.addLink(e[0], e[1])

    def get_switches_with_hosts(self):
        return self.switch_names

    def __str__(self):
        params_str = ''
        for k, v in self.params.items():
            params_str += "_" + str(k) + "_" + str(v)
        return self.__class__.__name__ + params_str
