__author__ = 'Rakesh Kumar'

import sys
import random
sys.path.append("./")

from analysis.flow_validator import FlowValidator

class MonteCarloAnalysis(FlowValidator):

    def __init__(self, network_graph):
        super(MonteCarloAnalysis, self).__init__(network_graph)

    def process_link_status_change(self, verbose=True):

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
                    print "Disconnected Flow: src_h_id:", src_h_id,  "dst_h_id:", dst_h_id
                else:
                    if path_vuln_ranks[0] > 0:
                        print "Vulnerable Flow: src_h_id:", src_h_id,  "dst_h_id:", dst_h_id

        return all_pair_connected

    # Return number of edges it took to break
    def break_random_edges_until_pair_disconnected(self, src_h_id, dst_h_id, verbose):
        edges_broken = []

        specific_traffic = self.get_specific_traffic(src_h_id, dst_h_id)
        at, all_paths, path_vuln_ranks = self.validate_host_pair_reachability(src_h_id,
                                                                              dst_h_id,
                                                                              specific_traffic,
                                                                              verbose)

        orig_at = at
        orig_all_paths = all_paths

        while all_paths:

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
            at, all_paths, path_vuln_ranks = self.validate_host_pair_reachability(src_h_id, dst_h_id,
                                                                                  specific_traffic, verbose)

        # Restore the edges for next run
        for edge in edges_broken:
            self.port_graph.add_node_graph_edge(edge[0], edge[1], updating=True)

        if verbose:
            print "edges_broken:", edges_broken

        # For comparison sake:
        now_at, now_all_paths, path_vuln_ranks = self.validate_host_pair_reachability(src_h_id, dst_h_id,
                                                                                      specific_traffic, verbose)

        if now_all_paths != orig_all_paths or not(orig_at.is_subset_traffic(now_at)):
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

            # if not self.is_edge_vulnerable(sampled_edge) and edges_broken:
            #     continue

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

        all_pair_connected = self.process_link_status_change(verbose)

        for edge in edges:

            # Break the edge
            edges_broken.append(edge)
            self.port_graph.remove_node_graph_edge(edge[0], edge[1])
            all_pair_connected = self.process_link_status_change(verbose)

        # Restore the edges for next run
        for edge in edges_broken:
            self.port_graph.add_node_graph_edge(edge[0], edge[1], updating=True)
            all_pair_connected = self.process_link_status_change(verbose)

        if verbose:
            print "edges_broken:", edges_broken

        return edges_broken