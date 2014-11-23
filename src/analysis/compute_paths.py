__author__ = 'Rakesh Kumar'

import networkx as nx
import sys

from model.model import Model
from model.match import Match

from netaddr import IPNetwork

class ComputePaths:
    def __init__(self):
        self.model = Model()

    def dfs(self, node_obj, destination_node_obj, visited):

        visited.add(node_obj)

        for neighbor in self.model.graph.neighbors(node_obj.node_id):
            neighbor_obj = self.model.get_node_object(neighbor)

            # If haven't been to this neighbor before
            if neighbor_obj not in visited:

                # See if we can get to this neighbor from here with the match
                edge_port_dict = self.model.get_edge_port_dict(node_obj.node_id, neighbor)
                out_port_match = node_obj.transfer_function(node_obj.in_port_match)
                if edge_port_dict[node_obj.node_id] in out_port_match:

                    passing_match = out_port_match[edge_port_dict[node_obj.node_id]]
                    passing_match.in_port = edge_port_dict[neighbor]
                    neighbor_obj.in_port_match = passing_match

                    if neighbor_obj.node_id == destination_node_obj.node_id:
                        print "Arrived at the destination."
                    else:
                        self.dfs(neighbor_obj, destination_node_obj, visited)


    def bfs(self, start_node_obj, destination_node_obj):

        visited = set()
        queue =[start_node_obj]

        while queue:
            node_obj = queue.pop(0)

            if node_obj == destination_node_obj:
                print "Arrived at the destination:", node_obj.node_id
            else:
                print "Exploring node:", node_obj.node_id

            if node_obj not in visited:
                visited.add(node_obj)

                # Go through the neighbors of this node and see where else we can go
                for neighbor in self.model.graph.neighbors(node_obj.node_id):
                    neighbor_obj = self.model.get_node_object(neighbor)
                    if neighbor_obj not in visited:

                        # See if we can get to this neighbor from here with the match
                        edge_port_dict = self.model.get_edge_port_dict(node_obj.node_id, neighbor)
                        out_port_match = node_obj.transfer_function(node_obj.in_port_match)
                        if edge_port_dict[node_obj.node_id] in out_port_match:

                            # Account for what traffic will arrive at neighbor
                            passing_match = out_port_match[edge_port_dict[node_obj.node_id]]
                            passing_match.in_port = edge_port_dict[neighbor]
                            neighbor_obj.in_port_match = passing_match

                            # Add the neighbor to queue so it is visited
                            queue.append(neighbor_obj)



    def analyze_all_node_pairs(self):

        # For each host, start a graph search at the switch it is connected to
        for src_h_id in self.model.get_host_ids():

            for dst_h_id in self.model.get_host_ids():

                src_h_obj = self.model.get_node_object(src_h_id)
                dst_h_obj = self.model.get_node_object(dst_h_id)

                if src_h_id == dst_h_id:
                    continue

                print "Injecting wildcard at switch:", src_h_obj.switch_obj, "connected to host", src_h_id

                src_h_obj.switch_obj.in_port_match = Match()
                src_h_obj.switch_obj.in_port_match.ethernet_type = 0x0800
                src_h_obj.switch_obj.in_port_match.ethernet_source = src_h_obj.mac_addr
                src_h_obj.switch_obj.in_port_match.ethernet_destination = dst_h_obj.mac_addr
                src_h_obj.switch_obj.in_port_match.has_vlan_tag = False
                src_h_obj.switch_obj.in_port = src_h_obj.switch_port_attached

                print "--"
                self.dfs(src_h_obj.switch_obj, dst_h_obj, set())

                #self.bfs(src_h_obj.switch_obj, dst_h_obj)

def main():
    bp = ComputePaths()
    bp.analyze_all_node_pairs()


if __name__ == "__main__":
    main()
