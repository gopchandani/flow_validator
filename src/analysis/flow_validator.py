__author__ = 'Rakesh Kumar'

import sys
import random
sys.path.append("./")

from model.port_graph import PortGraph
from model.traffic import Traffic, TrafficElement
from model.match import Match

class FlowValidator:

    def __init__(self, network_graph):
        self.network_graph = network_graph
        self.port_graph = PortGraph(network_graph)

    def init_port_graph(self):
        self.port_graph.init_port_graph()

    def de_init_port_graph(self):
        self.port_graph.de_init_port_graph()

    def add_hosts(self):

        # Attach a destination port for each host.
        for host_id in self.network_graph.get_experiment_host_ids():

            host_obj = self.network_graph.get_node_object(host_id)
            host_obj.switch_ingress_port = self.port_graph.get_port(host_obj.switch_id +
                                                                    ":ingress" + str(host_obj.switch_port_attached))
            host_obj.switch_egress_port = self.port_graph.get_port(host_obj.switch_id +
                                                                   ":egress" + str(host_obj.switch_port_attached))

    def remove_hosts(self):

        for host_id in self.network_graph.get_experiment_host_ids():
            host_obj = self.network_graph.get_node_object(host_id)
            self.port_graph.remove_node_graph_edge(host_id, host_obj.switch_id)

    def initialize_admitted_traffic(self):

        for host_id in self.network_graph.get_experiment_host_ids():
            host_obj = self.network_graph.get_node_object(host_id)

            admitted_traffic = Traffic(init_wildcard=True)
            admitted_traffic.set_field("ethernet_type", 0x0800)
            dst_mac_int = int(host_obj.mac_addr.replace(":", ""), 16)
            admitted_traffic.set_field("ethernet_destination", dst_mac_int)

            self.port_graph.compute_admitted_traffic(host_obj.switch_egress_port,
                                                     admitted_traffic,
                                                     None,
                                                     host_obj.switch_egress_port)

    def validate_host_pair_reachability(self, src_h_id, dst_h_id, verbose=True, specific_traffic=None):

        at = None

        src_host_obj = self.network_graph.get_node_object(src_h_id)
        dst_host_obj = self.network_graph.get_node_object(dst_h_id)

        path_count = self.port_graph.count_paths(src_host_obj.switch_ingress_port,
                                    dst_host_obj.switch_egress_port,
                                    verbose,
                                    path_str=src_host_obj.switch_ingress_port.port_id,
                                                 path_elements=[src_host_obj.switch_ingress_port.port_id])

        at = src_host_obj.switch_ingress_port.get_dst_admitted_traffic(dst_host_obj.switch_egress_port)
        if not at.is_empty() and verbose:
            print "Number of traffic elements in admitted traffic:", len(at.traffic_elements)
            
            if specific_traffic:
                if not at.is_subset_traffic(specific_traffic):
                    at = None
                    path_count = 0    

        return at, path_count

    def validate_all_host_pair_reachability(self, verbose=True, specific_traffic=False):

        all_pair_connected = True

        for src_h_id in self.network_graph.get_experiment_host_ids():
            for dst_h_id in self.network_graph.get_experiment_host_ids():

                if src_h_id == dst_h_id:
                    continue

                if specific_traffic:

                    src_h_obj = self.network_graph.get_node_object(src_h_id)
                    dst_h_obj = self.network_graph.get_node_object(dst_h_id)

                    specific_traffic = Traffic()
                    specific_match = Match(is_wildcard=True)
                    specific_match["ethernet_type"] = 0x0800
                    specific_match["ethernet_destination"] = int(dst_h_obj.mac_addr.replace(":", ""), 16)
                    specific_match["in_port"] = int(src_h_obj.switch_port_attached)

                    specific_te = TrafficElement(init_match=specific_match)
                    specific_te.match_fields["vlan_id"].chop(src_h_obj.switch_obj.synthesis_tag,
                                                             src_h_obj.switch_obj.synthesis_tag + 1)

                    specific_traffic.add_traffic_elements([specific_te])

                baseline_at, baseline_path_count = self.validate_host_pair_reachability(src_h_id, dst_h_id,
                                                                                        verbose,
                                                                                        specific_traffic)

                if not baseline_path_count:
                    all_pair_connected = False

        return all_pair_connected

    def validate_all_host_pair_backup(self, verbose=True):

        for src_h_id in self.network_graph.get_experiment_host_ids():
            for dst_h_id in self.network_graph.get_experiment_host_ids():

                if src_h_id == dst_h_id:
                    continue

                baseline_at, baseline_path_count = self.validate_host_pair_reachability(src_h_id,
                                                                                        dst_h_id,
                                                                                        verbose)

                # Now break the edges in the network graph, one-by-one
                for edge in self.network_graph.graph.edges():

                    if edge[0].startswith("h") or edge[1].startswith("h"):
                        continue

                    if verbose:
                        print "Failing edge:", edge

                    self.port_graph.remove_node_graph_edge(edge[0], edge[1])
                    edge_removed_at, edge_remove_path_count = self.validate_host_pair_reachability(src_h_id,
                                                                                                   dst_h_id,
                                                                                                   verbose)
                    if verbose:
                        print "Restoring edge:", edge

                    # Add it back
                    self.port_graph.add_node_graph_edge(edge[0], edge[1], updating=True)
                    edge_added_back_at, edge_added_back_path_count = self.validate_host_pair_reachability(src_h_id,
                                                                                                          dst_h_id,
                                                                                                          verbose)

                    # the number of elements should be same in three scenarios for each edge

                    if not(baseline_at.is_subset_traffic(edge_removed_at) and
                               edge_added_back_at.is_subset_traffic(edge_removed_at)):
                        print "Backup doesn't exist for:", src_h_id, "->", dst_h_id, "due to edge:", edge

    #Return number of edges it took to break
    def break_random_edges_until_pair_disconnected(self, src_h_id, dst_h_id, verbose):
        edges_broken = []

        at, path_count = self.validate_host_pair_reachability(src_h_id, dst_h_id, verbose)

        orig_at = at
        orig_path_count = path_count

        while path_count:

            # Randomly sample an edge to break, sample again if it has already been broken
            edge = random.choice(self.network_graph.graph.edges())

            # Ignore host edges
            if edge[0].startswith("h") or edge[1].startswith("h"):
                continue

            if edge in edges_broken:
                continue

            # Break the edge
            edges_broken.append(edge)
            self.port_graph.remove_node_graph_edge(edge[0], edge[1])
            at, path_count = self.validate_host_pair_reachability(src_h_id, dst_h_id, verbose)

        # Restore the edges for next run
        for edge in edges_broken:
            self.port_graph.add_node_graph_edge(edge[0], edge[1], updating=True)

        if verbose:
            print "edges_broken:", edges_broken

        # For comparison sake:
        now_at, now_path_count = self.validate_host_pair_reachability(src_h_id, dst_h_id, verbose)

        if now_path_count != orig_path_count or not(orig_at.is_subset_traffic(now_at)):
            print "Something went wrong:", src_h_id, "<->", dst_h_id, "due to edges_broken:", edges_broken

        return len(edges_broken)

    def break_random_edges_until_any_pair_disconnected(self, verbose):
        edges_broken = []

        all_pair_connected = self.validate_all_host_pair_reachability(verbose, specific_traffic=True)

        while all_pair_connected:

            # Randomly sample an edge to break, sample again if it has already been broken
            edge = random.choice(self.network_graph.graph.edges())

            # Ignore host edges
            if edge[0].startswith("h") or edge[1].startswith("h"):
                continue

            if edge in edges_broken:
                continue

            if verbose:
                print "Breaking the edge:", edge

            # Break the edge
            edges_broken.append(edge)
            self.port_graph.remove_node_graph_edge(edge[0], edge[1])
            all_pair_connected = self.validate_all_host_pair_reachability(verbose)

        # Restore the edges for next run
        for edge in edges_broken:
            self.port_graph.add_node_graph_edge(edge[0], edge[1], updating=True)

        all_pair_connected = self.validate_all_host_pair_reachability(verbose, specific_traffic=True)

        if verbose:
            print "edges_broken:", edges_broken

        return edges_broken

    def break_specified_edges_in_order(self, edges, verbose):

        edges_broken = []

        all_pair_connected = self.validate_all_host_pair_reachability(verbose, specific_traffic=True)

        for edge in edges:

            # Break the edge
            edges_broken.append(edge)
            self.port_graph.remove_node_graph_edge(edge[0], edge[1])
            all_pair_connected = self.validate_all_host_pair_reachability(verbose)

        # Restore the edges for next run
        for edge in edges_broken:
            self.port_graph.add_node_graph_edge(edge[0], edge[1], updating=True)
            all_pair_connected = self.validate_all_host_pair_reachability(verbose, specific_traffic=True)

        if verbose:
            print "edges_broken:", edges_broken

        return edges_broken, all_pair_connected

