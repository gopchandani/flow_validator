__author__ = 'Rakesh Kumar'

import sys
import random
sys.path.append("./")

from analysis.flow_validator import FlowValidator

class MonteCarloAnalysis(FlowValidator):

    def __init__(self, network_graph):
        super(MonteCarloAnalysis, self).__init__(network_graph)

        self.links_broken = []

    def initialize_per_link_traffic_paths(self, verbose=False):

        for ld in self.network_graph.get_switch_link_data():
            del ld.traffic_paths[:]

        for src_h_id in self.network_graph.host_ids:
            for dst_h_id in self.network_graph.host_ids:

                if src_h_id == dst_h_id:
                    continue

                src_host_obj = self.network_graph.get_node_object(src_h_id)
                dst_host_obj = self.network_graph.get_node_object(dst_h_id)

                specific_traffic = self.get_specific_traffic(src_h_id, dst_h_id)

                all_paths = self.port_graph.get_paths(src_host_obj.switch_ingress_port,
                                                      dst_host_obj.switch_egress_port,
                                                      specific_traffic,
                                                      [src_host_obj.switch_ingress_port],
                                                      [],
                                                      verbose)

                for path in all_paths:
                    if verbose:
                        print "src_h_id:", src_h_id, "dst_h_id:", dst_h_id, "path:", path

                    path_links = path.get_path_links()
                    for path_link in path_links:
                        ld = self.network_graph.get_link_data(path_link[0], path_link[1])

                        # Avoid adding the same path twice for cases when a link is repeated
                        if path not in ld.traffic_paths:
                            ld.traffic_paths.append(path)

    def classify_network_graph_links(self):

        # Go through every switch-switch link
        for ld in self.network_graph.get_switch_link_data():

            if ld.forward_link in self.links_broken or ld.reverse_link in self.links_broken:
                continue

            ld.causes_disconnect = False
            print "Considering Failure of Link:", ld.forward_link

            # For each primary traffic path that goes through that link, check
            for path in ld.traffic_paths:

                print path.get_max_vuln_rank(), path.get_max_active_rank()

                # Check to see if the path is primary
                #if not path.max_vuln_rank:

                if path.get_max_active_rank() == 0:

                    print "Considering Path: ", path

                    if path.link_failure_causes_disconnect(ld):
                        ld.causes_disconnect = True
                        break

            print "Causes Disconnect:", ld.causes_disconnect

    def check_all_host_pair_connected(self, verbose=True):

        all_host_pair_connected = True

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
                    all_host_pair_connected = False
                    print "Disconnected Flow: src_h_id:", src_h_id,  "dst_h_id:", dst_h_id

        return all_host_pair_connected

    # Return number of edges it took to break
    def break_random_edges_until_pair_disconnected(self, src_h_id, dst_h_id, verbose):
        del self.links_broken[:]

        specific_traffic = self.get_specific_traffic(src_h_id, dst_h_id)
        at, all_paths = self.validate_host_pair_reachability(src_h_id,
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

            if edge in self.links_broken:
                continue

            # Break the edge
            self.links_broken.append((str(edge[0]), str(edge[1])))
            self.port_graph.remove_node_graph_edge(edge[0], edge[1])
            at, all_paths = self.validate_host_pair_reachability(src_h_id,
                                                                 dst_h_id,
                                                                 specific_traffic,
                                                                 verbose)

        # Restore the edges for next run
        for edge in self.links_broken:
            self.port_graph.add_node_graph_edge(edge[0], edge[1], updating=True)

        if verbose:
            print "self.links_broken:", self.links_broken

        # For comparison sake:
        now_at, now_all_paths = self.validate_host_pair_reachability(src_h_id,
                                                                     dst_h_id,
                                                                     specific_traffic,
                                                                     verbose)

        if now_all_paths != orig_all_paths or not(orig_at.is_subset_traffic(now_at)):
            print "Something went wrong:", src_h_id, "<->", dst_h_id, "due to self.links_broken:", self.links_broken

        return len(self.links_broken)

    def sample_edge(self, importance=False):

        sampled_edge = None

        while True:

            # Randomly sample an edge to break, sample again if it has already been broken
            sampled_edge = random.choice(self.network_graph.graph.edges())

            # Ignore host edges
            if sampled_edge[0].startswith("h") or sampled_edge[1].startswith("h"):
                continue

            if sampled_edge in self.links_broken:
                continue

            break

        return sampled_edge

    def break_random_edges_until_any_pair_disconnected(self, verbose, importance=False):
        del self.links_broken[:]

        all_host_pair_connected = self.check_all_host_pair_connected(verbose)

        while all_host_pair_connected:

            # Randomly sample an edge to break, sample again if it has already been broken
            edge = self.sample_edge(importance)

            print "Breaking the edge:", edge

            # Break the edge
            self.links_broken.append((str(edge[0]), str(edge[1])))
            self.port_graph.remove_node_graph_edge(edge[0], edge[1])
            all_host_pair_connected = self.check_all_host_pair_connected(verbose)

            self.initialize_per_link_traffic_paths()
            self.classify_network_graph_links()

        # Restore the edges for next run
        for edge in self.links_broken:
            print "Restoring the edge:", edge
            self.port_graph.add_node_graph_edge(edge[0], edge[1], updating=True)

        all_host_pair_connected = self.check_all_host_pair_connected(verbose)

        self.initialize_per_link_traffic_paths()
        self.classify_network_graph_links()

        if verbose:
            print "self.links_broken:", self.links_broken

        return self.links_broken

    def break_specified_edges_in_order(self, edges, verbose):

        del self.links_broken[:]

        all_host_pair_connected = self.check_all_host_pair_connected(verbose)

        for edge in edges:

            # Break the edge
            self.links_broken.append((str(edge[0]), str(edge[1])))
            self.port_graph.remove_node_graph_edge(edge[0], edge[1])
            all_host_pair_connected = self.check_all_host_pair_connected(verbose)

        # Restore the edges for next run
        for edge in self.links_broken:
            self.port_graph.add_node_graph_edge(edge[0], edge[1], updating=True)
            all_host_pair_connected = self.check_all_host_pair_connected(verbose)

        if verbose:
            print "self.links_broken:", self.links_broken

        return self.links_broken