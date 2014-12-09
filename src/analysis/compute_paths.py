__author__ = 'Rakesh Kumar'

import networkx as nx
import sys

from model.model import Model
from model.match import Match

from netaddr import IPNetwork

class ComputePaths:
    def __init__(self):
        self.model = Model()

    def check_switch_crossing(self, neighbor_obj, node_obj, destination):

        print "At switch:", node_obj.node_id, "Neighbor Switch:", neighbor_obj.node_id

        edge_port_dict = self.model.get_edge_port_dict(neighbor_obj.node_id, node_obj.node_id)

        #Check to see if the required destination match can get from neighbor to node
        out_port_match = neighbor_obj.transfer_function(node_obj.accepted_destination_match[destination])

        if edge_port_dict[neighbor_obj.node_id] in out_port_match:

            # compute what traffic will arrive from neighbor
            passing_match = out_port_match[edge_port_dict[neighbor_obj.node_id]]

            # Set the match in the neighbor, indicating what passes
            neighbor_obj.accepted_destination_match[destination] = passing_match

            return True
        else:
            return False

    def bfs_paths(self, start_node_obj, destination_node_obj, destination):

        queue = [(destination_node_obj, [destination_node_obj])]

        while queue:
            node_obj, path = queue.pop(0)

            for neighbor in self.model.graph.neighbors(node_obj.node_id):
                neighbor_obj = self.model.get_node_object(neighbor)

                # Consider only nodes that are not in the path accumulated so far
                if neighbor_obj not in path:

                    # If arrived at the source already, stop
                    if neighbor_obj == start_node_obj:
                        yield [neighbor_obj] + path

                    # Otherwise, can I come from neighbor to here
                    else:
                        if self.check_switch_crossing(neighbor_obj, node_obj, destination):
                            queue.append((neighbor_obj, [neighbor_obj] + path))

    def analyze_all_node_pairs(self):

        # For each host, start a graph search at the switch it is connected to
        for src_h_id in self.model.get_host_ids():

            for dst_h_id in self.model.get_host_ids():

                src_h_obj = self.model.get_node_object(src_h_id)
                dst_h_obj = self.model.get_node_object(dst_h_id)

                if src_h_id == dst_h_id:
                    continue

                print "Setting accepted destination at switch:", dst_h_obj.switch_obj, "connected to host", dst_h_id

                accepted_match = Match()
                accepted_match.ethernet_type = 0x0800
                accepted_match.ethernet_source = src_h_obj.mac_addr
                accepted_match.ethernet_destination = dst_h_obj.mac_addr
                
                dst_h_obj.switch_obj.accepted_destination_match[dst_h_obj.node_id] = accepted_match

                print "--"
                print list(self.bfs_paths(src_h_obj.switch_obj, dst_h_obj.switch_obj, dst_h_id))


    def tf_driver(self):
        for sw in self.model.get_switches():
            print sw.node_id
            sw.compute_transfer_function()


def main():
    bp = ComputePaths()
    #bp.analyze_all_node_pairs()

    bp.analyze_all_node_pairs()

    #bp.tf_driver()


if __name__ == "__main__":
    main()
