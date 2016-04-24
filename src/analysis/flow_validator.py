__author__ = 'Rakesh Kumar'

import sys
import random
sys.path.append("./")

from collections import defaultdict

from model.network_port_graph import NetworkPortGraph
from model.traffic import Traffic

class FlowValidator(object):

    def __init__(self, network_graph):
        self.network_graph = network_graph
        self.port_graph = NetworkPortGraph(network_graph)

    def init_network_port_graph(self):
        self.port_graph.init_network_port_graph()

    def de_init_network_port_graph(self):
        self.port_graph.de_init_network_port_graph()

    def add_hosts(self):

        # Attach a destination port for each host.
        for host_id in self.network_graph.host_ids:

            host_obj = self.network_graph.get_node_object(host_id)
            host_obj.switch_ingress_port = self.port_graph.get_node(host_obj.switch_id +
                                                                    ":ingress" + str(host_obj.switch_port_attached))
            host_obj.switch_egress_port = self.port_graph.get_node(host_obj.switch_id +
                                                                   ":egress" + str(host_obj.switch_port_attached))

    def remove_hosts(self):

        for host_id in self.network_graph.host_ids:
            host_obj = self.network_graph.get_node_object(host_id)
            self.port_graph.remove_node_graph_link(host_id, host_obj.switch_id)

    def initialize_admitted_traffic(self):

        for host_id in self.network_graph.host_ids:
            host_obj = self.network_graph.get_node_object(host_id)

            dst_traffic_at_succ = Traffic(init_wildcard=True)
            dst_traffic_at_succ.set_field("ethernet_type", 0x0800)
            dst_mac_int = int(host_obj.mac_addr.replace(":", ""), 16)
            dst_traffic_at_succ.set_field("ethernet_destination", dst_mac_int)

            print "Initializing for host:", host_id

            end_to_end_modified_edges = []

            self.port_graph.compute_admitted_traffic(host_obj.switch_egress_port,
                                                     dst_traffic_at_succ,
                                                     None,
                                                     host_obj.switch_egress_port,
                                                     end_to_end_modified_edges)

    def validate_host_pair_reachability(self, src_h_id, dst_h_id, specific_traffic, verbose=True):

        src_host_obj = self.network_graph.get_node_object(src_h_id)
        dst_host_obj = self.network_graph.get_node_object(dst_h_id)

        at = self.port_graph.get_admitted_traffic(src_host_obj.switch_ingress_port, dst_host_obj.switch_egress_port)
        all_paths = []

        if not at.is_empty():

            if verbose:
                print "-------------------"
                print src_h_id, "->", dst_h_id
                print "Number of traffic elements in admitted traffic:", len(at.traffic_elements)
                print at

            if at.is_subset_traffic(specific_traffic):

                all_paths = self.port_graph.get_paths(src_host_obj.switch_ingress_port,
                                                      dst_host_obj.switch_egress_port,
                                                      specific_traffic,
                                                      [src_host_obj.switch_ingress_port],
                                                      [],
                                                      verbose)

            else:
                if verbose:
                    print "src_h_id:", src_h_id, "dst_h_id:", dst_h_id, "at does not pass specific_traffic check."
        else:
            if verbose:
                print "src_h_id:", src_h_id, "dst_h_id:", dst_h_id, "at is empty."

        return at, all_paths

    def get_all_host_pairs_traffic_paths(self, verbose=False):

        host_pair_paths = defaultdict(defaultdict)

        for src_h_id in self.network_graph.host_ids:
            for dst_h_id in self.network_graph.host_ids:

                if src_h_id == dst_h_id:
                    continue

                specific_traffic = self.get_specific_traffic(src_h_id, dst_h_id)

                at, all_paths = self.validate_host_pair_reachability(src_h_id,
                                                                     dst_h_id,
                                                                     specific_traffic,
                                                                     verbose)
                if not all_paths:
                    host_pair_paths[src_h_id][dst_h_id] = []
                else:
                    host_pair_paths[src_h_id][dst_h_id] = all_paths

        return host_pair_paths

    def validate_all_host_pair_reachability(self, verbose=True):

        all_pair_connected = True

        for src_h_id in self.network_graph.host_ids:
            for dst_h_id in self.network_graph.host_ids:

                if src_h_id == dst_h_id:
                    continue

                if verbose:
                    print "src_h_id:", src_h_id,  "dst_h_id:", dst_h_id

                specific_traffic = self.get_specific_traffic(src_h_id, dst_h_id)

                at, all_paths = self.validate_host_pair_reachability(src_h_id,
                                                                     dst_h_id,
                                                                     specific_traffic,
                                                                     verbose)
                if not all_paths:
                    all_pair_connected = False

        return all_pair_connected

    def validate_host_pair_backup(self, src_h_id, dst_h_id, verbose=True):
        specific_traffic = self.get_specific_traffic(src_h_id, dst_h_id)

        baseline_at, baseline_all_paths = self.validate_host_pair_reachability(src_h_id,
                                                                               dst_h_id,
                                                                               specific_traffic,
                                                                               verbose)

        # Now break the edges in the network graph, one-by-one
        for edge in self.network_graph.graph.edges():

            if edge[0].startswith("h") or edge[1].startswith("h"):
                continue

            if verbose:
                print "Failing edge:", edge

            self.port_graph.remove_node_graph_link(edge[0], edge[1])
            edge_removed_at, edge_removed_all_paths = self.validate_host_pair_reachability(src_h_id,
                                                                                           dst_h_id,
                                                                                           specific_traffic,
                                                                                           verbose)
            if verbose:
                print "Restoring edge:", edge

            # Add it back
            self.port_graph.add_node_graph_link(edge[0], edge[1], updating=True)
            edge_added_back_at, edge_added_back_all_paths = self.validate_host_pair_reachability(src_h_id,
                                                                                                 dst_h_id,
                                                                                                 specific_traffic,
                                                                                                 verbose)

            # The number of elements should be same in three scenarios for each edge

            if not(baseline_at.is_subset_traffic(edge_removed_at) and
                       edge_added_back_at.is_subset_traffic(edge_removed_at)):
                print "Backup doesn't exist for:", src_h_id, "->", dst_h_id, "due to edge:", edge

    def validate_all_host_pair_backup(self, src_host_ids, dst_host_ids, verbose=True):

        for src_h_id in src_host_ids:
            for dst_h_id in dst_host_ids:

                if src_h_id == dst_h_id:
                    continue

                self.validate_host_pair_backup(src_h_id, dst_h_id)

    def get_specific_traffic(self, src_h_id, dst_h_id):

        src_h_obj = self.network_graph.get_node_object(src_h_id)
        dst_h_obj = self.network_graph.get_node_object(dst_h_id)

        specific_traffic = Traffic(init_wildcard=True)
        specific_traffic.set_field("ethernet_type", 0x0800)
        specific_traffic.set_field("ethernet_source", int(src_h_obj.mac_addr.replace(":", ""), 16))
        specific_traffic.set_field("ethernet_destination", int(dst_h_obj.mac_addr.replace(":", ""), 16))
        specific_traffic.set_field("in_port", int(src_h_obj.switch_port_attached))
        specific_traffic.set_field("vlan_id", src_h_obj.switch_obj.synthesis_tag, is_exception_value=True)

        return specific_traffic