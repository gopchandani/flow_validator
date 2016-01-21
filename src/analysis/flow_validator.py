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
        for host_id in self.network_graph.host_ids:

            host_obj = self.network_graph.get_node_object(host_id)
            host_obj.switch_ingress_port = self.port_graph.get_port(host_obj.switch_id +
                                                                    ":ingress" + str(host_obj.switch_port_attached))
            host_obj.switch_egress_port = self.port_graph.get_port(host_obj.switch_id +
                                                                   ":egress" + str(host_obj.switch_port_attached))

    def remove_hosts(self):

        for host_id in self.network_graph.host_ids:
            host_obj = self.network_graph.get_node_object(host_id)
            self.port_graph.remove_node_graph_edge(host_id, host_obj.switch_id)

    def initialize_admitted_traffic(self):

        for host_id in self.network_graph.host_ids:
            host_obj = self.network_graph.get_node_object(host_id)

            admitted_traffic = Traffic(init_wildcard=True)
            admitted_traffic.set_field("ethernet_type", 0x0800)
            dst_mac_int = int(host_obj.mac_addr.replace(":", ""), 16)
            admitted_traffic.set_field("ethernet_destination", dst_mac_int)

            self.port_graph.compute_admitted_traffic(host_obj.switch_egress_port,
                                                     admitted_traffic,
                                                     None,
                                                     host_obj.switch_egress_port)

    def validate_host_pair_reachability(self, src_h_id, dst_h_id, specific_traffic, verbose=True):

        src_host_obj = self.network_graph.get_node_object(src_h_id)
        dst_host_obj = self.network_graph.get_node_object(dst_h_id)

        at = src_host_obj.switch_ingress_port.get_dst_admitted_traffic(dst_host_obj.switch_egress_port)
        path_vuln_ranks = []
        all_paths = []

        if not at.is_empty():

            if verbose:
                print "Number of traffic elements in admitted traffic:", len(at.traffic_elements)

            if at.is_subset_traffic(specific_traffic):

                self.port_graph.get_paths(src_host_obj.switch_ingress_port,
                                          dst_host_obj.switch_egress_port,
                                          specific_traffic,
                                          [src_host_obj.switch_ingress_port],
                                          all_paths,
                                          0,
                                          path_vuln_ranks,
                                          verbose)

                if verbose:
                    print "Path vulnerability ranks:", path_vuln_ranks
            else:
                if verbose:
                    print "src_h_id:", src_h_id, "dst_h_id:", dst_h_id, "at does not pass specific_traffic check."
        else:
            if verbose:
                print "src_h_id:", src_h_id, "dst_h_id:", dst_h_id, "at is empty."

        return at, all_paths, path_vuln_ranks

    def validate_all_host_pair_reachability(self, verbose=True):

        all_pair_connected = True

        for src_h_id in self.network_graph.host_ids:
            for dst_h_id in self.network_graph.host_ids:

                if src_h_id == dst_h_id:
                    continue

                if verbose:
                    print "src_h_id:", src_h_id,  "dst_h_id:", dst_h_id

                specific_traffic = self.get_specific_traffic(src_h_id, dst_h_id)

                at, all_paths, path_vuln_ranks = self.validate_host_pair_reachability(src_h_id,
                                                                                       dst_h_id,
                                                                                       specific_traffic,
                                                                                       verbose)
                if not all_paths:
                    all_pair_connected = False

        return all_pair_connected

    def process_link_status_change(self, verbose=True):

        all_pair_connected = True

        for e in self.network_graph.graph.edges_iter():
            self.network_graph.graph[e[0]][e[1]]["vuln_info"].clear()

        for src_h_id in self.network_graph.host_ids:
            for dst_h_id in self.network_graph.host_ids:

                if src_h_id == dst_h_id:
                    continue

                if src_h_id == 'h131' and dst_h_id == 'h101':
                    pass

                if verbose:
                    print "src_h_id:", src_h_id,  "dst_h_id:", dst_h_id

                specific_traffic = self.get_specific_traffic(src_h_id, dst_h_id)

                at, all_paths, path_vuln_ranks = self.validate_host_pair_reachability(src_h_id,
                                                                                       dst_h_id,
                                                                                       specific_traffic,
                                                                                       verbose)
                if not all_paths:
                    all_pair_connected = False
                    print "Disconnected Flow: src_h_id:", src_h_id,  "dst_h_id:", dst_h_id
                else:
                    if path_vuln_ranks[0] > 0:
                        print "Vulnerable Flow: src_h_id:", src_h_id,  "dst_h_id:", dst_h_id

                    path = all_paths[0]
                    prev_switch = path[0].sw.node_id
                    for this_path_element in path[1:]:
                        this_switch = this_path_element.sw.node_id

                        if prev_switch != this_switch:
                            self.network_graph.graph[prev_switch][this_switch]\
                                ["vuln_info"][path_vuln_ranks[0]].append(path)

                        prev_switch = this_switch

        return all_pair_connected

    def validate_all_host_pair_backup(self, verbose=True):

        for src_h_id in self.network_graph.host_ids:
            for dst_h_id in self.network_graph.host_ids:

                if src_h_id == dst_h_id:
                    continue

                specific_traffic = self.get_specific_traffic(src_h_id, dst_h_id)

                baseline_at, baseline_all_paths, baseline_path_vuln_ranks = \
                    self.validate_host_pair_reachability(src_h_id,
                                                         dst_h_id,
                                                         specific_traffic,
                                                         verbose)

                # Now break the edges in the network graph, one-by-one
                for edge in self.network_graph.graph.edges():

                    if edge[0].startswith("h") or edge[1].startswith("h"):
                        continue

                    if verbose:
                        print "Failing edge:", edge

                    self.port_graph.remove_node_graph_edge(edge[0], edge[1])
                    edge_removed_at, edge_removed_all_paths, edge_removed_path_vuln_ranks = \
                        self.validate_host_pair_reachability(src_h_id,
                                                             dst_h_id,
                                                             specific_traffic,
                                                             verbose)
                    if verbose:
                        print "Restoring edge:", edge

                    # Add it back
                    self.port_graph.add_node_graph_edge(edge[0], edge[1], updating=True)
                    edge_added_back_at, edge_added_back_all_paths, edge_added_back_path_vuln_ranks = \
                        self.validate_host_pair_reachability(src_h_id,
                                                             dst_h_id,
                                                             specific_traffic,
                                                             verbose)

                    # the number of elements should be same in three scenarios for each edge

                    if not(baseline_at.is_subset_traffic(edge_removed_at) and
                               edge_added_back_at.is_subset_traffic(edge_removed_at)):
                        print "Backup doesn't exist for:", src_h_id, "->", dst_h_id, "due to edge:", edge

    def get_specific_traffic(self, src_h_id, dst_h_id):

        src_h_obj = self.network_graph.get_node_object(src_h_id)
        dst_h_obj = self.network_graph.get_node_object(dst_h_id)

        specific_traffic = Traffic()
        specific_match = Match(is_wildcard=True)
        specific_match["ethernet_type"] = 0x0800
        specific_match["ethernet_source"] = int(src_h_obj.mac_addr.replace(":", ""), 16)
        specific_match["ethernet_destination"] = int(dst_h_obj.mac_addr.replace(":", ""), 16)
        specific_match["in_port"] = int(src_h_obj.switch_port_attached)

        specific_te = TrafficElement(init_match=specific_match)
        specific_te.match_fields["vlan_id"].chop(src_h_obj.switch_obj.synthesis_tag,
                                                 src_h_obj.switch_obj.synthesis_tag + 1)

        specific_traffic.add_traffic_elements([specific_te])

        return specific_traffic

    # Return number of edges it took to break
    def break_random_edges_until_pair_disconnected(self, src_h_id, dst_h_id, verbose):
        edges_broken = []

        at, path_count, path_vuln_ranks = self.validate_host_pair_reachability(src_h_id, dst_h_id, verbose)

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
            at, path_count, path_vuln_ranks = self.validate_host_pair_reachability(src_h_id, dst_h_id, verbose)

        # Restore the edges for next run
        for edge in edges_broken:
            self.port_graph.add_node_graph_edge(edge[0], edge[1], updating=True)

        if verbose:
            print "edges_broken:", edges_broken

        # For comparison sake:
        now_at, now_path_count, path_vuln_ranks = self.validate_host_pair_reachability(src_h_id, dst_h_id, verbose)

        if now_path_count != orig_path_count or not(orig_at.is_subset_traffic(now_at)):
            print "Something went wrong:", src_h_id, "<->", dst_h_id, "due to edges_broken:", edges_broken

        return len(edges_broken)

    def is_edge_vulnerable(self, e):
        return 1 in self.network_graph.graph[e[0]][e[1]]["vuln_info"]

    def sample_edge(self, edges_broken, importance=False):

        sampled_edge = None

        while True:

            # Randomly sample an edge to break, sample again if it has already been broken
            sampled_edge = random.choice(self.network_graph.graph.edges())

            # Ignore host edges
            if sampled_edge[0].startswith("h") or sampled_edge[1].startswith("h"):
                continue

            if sampled_edge in edges_broken:
                continue

            if not self.is_edge_vulnerable(sampled_edge) and edges_broken:
                continue

            break

        return sampled_edge

    def break_random_edges_until_any_pair_disconnected(self, verbose, importance=False):
        edges_broken = []

        all_pair_connected = self.process_link_status_change(verbose)

        while all_pair_connected:

            # Randomly sample an edge to break, sample again if it has already been broken
            edge = self.sample_edge(edges_broken, importance)

            print "Breaking the edge:", edge

            # Break the edge
            edges_broken.append(edge)
            self.port_graph.remove_node_graph_edge(edge[0], edge[1])
            all_pair_connected = self.process_link_status_change(verbose)

        # Restore the edges for next run
        for edge in edges_broken:
            print "Restoring the edge:", edge
            self.port_graph.add_node_graph_edge(edge[0], edge[1], updating=True)

        all_pair_connected = self.process_link_status_change(verbose)

        if verbose:
            print "edges_broken:", edges_broken

        return edges_broken

    def break_specified_edges_in_order(self, edges, verbose):

        edges_broken = []

        all_pair_connected = self.validate_all_host_pair_reachability(verbose)
        self.process_link_status_change(verbose)

        for edge in edges:

            # Break the edge
            edges_broken.append(edge)
            self.port_graph.remove_node_graph_edge(edge[0], edge[1])
            all_pair_connected = self.validate_all_host_pair_reachability(verbose)

        # Restore the edges for next run
        for edge in edges_broken:
            self.port_graph.add_node_graph_edge(edge[0], edge[1], updating=True)
            all_pair_connected = self.validate_all_host_pair_reachability(verbose)

        if verbose:
            print "edges_broken:", edges_broken

        return edges_broken, all_pair_connected