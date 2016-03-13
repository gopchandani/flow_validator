__author__ = 'Rakesh Kumar'

import sys
import random
sys.path.append("./")

from analysis.flow_validator import FlowValidator

class MonteCarloAnalysis(FlowValidator):

    def __init__(self, network_graph):
        super(MonteCarloAnalysis, self).__init__(network_graph)

        self.links_broken = []
        self.all_links = []
        self.links_causing_disconnect = []
        self.links_not_causing_disconnect = []

        # Contains for each step (link failure), the alpha that was considered in computation
        self.alpha = []

        # Contains for each step (link failure), the size of set of links causing disconnect
        self.size_links_causing_disconnect = []

        # Contains for each step (link failure), the size of set of links not causing disconnect
        self.size_links_not_causing_disconnect = []

        # Total number of links (a constant)
        self.N = len(list(self.network_graph.get_switch_link_data())) * 1.0

    def initialize_per_link_traffic_paths(self, verbose=False):

        for ld in self.network_graph.get_switch_link_data():
            ld.traffic_paths = []

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

    def classify_network_graph_links(self, verbose=False):

        self.links_not_causing_disconnect = []
        self.links_causing_disconnect = []
        self.all_links = []

        # Go through every switch-switch link
        for ld in self.network_graph.get_switch_link_data():

            if ld.forward_link in self.links_broken or ld.reverse_link in self.links_broken:
                continue

            ld.causes_disconnect = False
            if verbose:
                print "Considering Failure of Link:", ld.forward_link

            # For each primary traffic path that goes through that link, check
            for path in ld.traffic_paths:

                # Check to see if the path is current active
                if path.get_max_active_rank() == 0:

                    if verbose:
                        print "Considering Path: ", path

                    if path.link_failure_causes_disconnect(ld):
                        ld.causes_disconnect = True
                        break

            if ld.causes_disconnect:
                self.links_causing_disconnect.append(ld)
            else:
                self.links_not_causing_disconnect.append(ld)

            self.all_links.append(ld)

            if verbose:
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
    def break_random_links_until_pair_disconnected(self, src_h_id, dst_h_id, verbose):
        self.links_broken = []

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
            self.port_graph.remove_node_graph_link(edge[0], edge[1])
            at, all_paths = self.validate_host_pair_reachability(src_h_id,
                                                                 dst_h_id,
                                                                 specific_traffic,
                                                                 verbose)

        # Restore the edges for next run
        for edge in self.links_broken:
            self.port_graph.add_node_graph_link(edge[0], edge[1], updating=True)

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

    def get_alpha(self, u, b, j):

        #return 0.5

        alpha = None

        if j == b + 1:
            alpha = ((b + 1)/(u)) * ((self.size_links_causing_disconnect[b])/(self.N - b))
        elif j > b + 1:
            p = 1.0
            for i in xrange(0, j-2 + 1):
                p = p * ((self.size_links_not_causing_disconnect[i]) / ((1 - self.alpha[i+1]) * (self.N - i)))

            alpha = (j/u) * ((self.size_links_causing_disconnect[j-1]) / (self.N - j + 1)) * (p)
        else:
            alpha = 0.0

        if alpha < 0.1:
            pass

        print "alpha:", alpha

        return alpha

    def sample_link_uniform(self):

        # Randomly sample a link to break
        sampled_ld = random.choice(self.all_links)
        sampled_link = sampled_ld.forward_link

        if sampled_link in self.links_broken:
            raise("Something wrong is happening with uniform link sampling")

        return sampled_link

    def sample_link_skewed(self, alpha):

        # Flip a coin
        unif = random.uniform(0, 1)

        if unif < alpha:
            sampled_ld = random.choice(self.links_causing_disconnect)
        else:
            sampled_ld = random.choice(self.links_not_causing_disconnect)

        sampled_link = sampled_ld.forward_link

        if sampled_link in self.links_broken:
            raise("Something wrong is happening with skewed link sampling")

        return sampled_link

    def get_importance_sampling_experiment_result(self, k):
        result = 0.0
        
        prod = 1.0
        
        for i in xrange(0, k-2 + 1):
            
            first_factor = (self.size_links_not_causing_disconnect[i]) / ((1 - self.alpha[i+1]) * (self.N - i))
            second_factor = (self.size_links_causing_disconnect[k-1]) / ((self.alpha[k]) * (self.N - k + 1))
            prod = prod * first_factor * second_factor
        
        result = k * prod

        if result > 100:
            pass

        return result

    def break_random_links_until_any_pair_disconnected(self, verbose, importance=False, u=None):
        self.links_broken = []
        self.alpha = []
        self.size_links_causing_disconnect = []
        self.size_links_not_causing_disconnect = []

        all_host_pair_connected = self.check_all_host_pair_connected(verbose)
        self.initialize_per_link_traffic_paths(verbose=False)
        self.classify_network_graph_links()

        b = None
        j = 0
        
        while all_host_pair_connected:

            if verbose:
                print "links_not_causing_disconnect:"
                for ld in self.links_not_causing_disconnect:
                    print ld

                print "links_causing_disconnect: "
                for ld in self.links_causing_disconnect:
                    print ld

            self.size_links_causing_disconnect.append(len(self.links_causing_disconnect))
            self.size_links_not_causing_disconnect.append(len(self.links_not_causing_disconnect))

            if b == None:
                self.alpha.append(0.0)

                if self.links_causing_disconnect:
                    # b is the smallest index j, for which self.links_causing_disconnect is empty
                    b = j
            else:
                if importance:
                    alpha = self.get_alpha(u, b, j)
                else:
                    alpha = None

                self.alpha.append(alpha)

            if importance:
                # Do a skewed sample when:
                # 1. There are links that can cause disconnect, thus you would skew to sample from them
                # 2. There are links that do not cause disconnect, otherwise skeweing is moot.

                if self.size_links_causing_disconnect[j] > 0 and self.size_links_not_causing_disconnect[j] > 0:
                    link = self.sample_link_skewed(self.alpha[j])
                else:
                    link = self.sample_link_uniform()
            else:
                link = self.sample_link_uniform()

            print "Breaking the link:", link

            # Break the link
            self.links_broken.append((str(link[0]), str(link[1])))
            self.port_graph.remove_node_graph_link(link[0], link[1])
            all_host_pair_connected = self.check_all_host_pair_connected(verbose)

            self.initialize_per_link_traffic_paths()
            self.classify_network_graph_links(verbose)

            j += 1

        # Restore the links for next run
        for link in self.links_broken:
            print "Restoring the link:", link
            self.port_graph.add_node_graph_link(link[0], link[1], updating=True)

        all_host_pair_connected = self.check_all_host_pair_connected(verbose)

        self.initialize_per_link_traffic_paths()
        self.classify_network_graph_links(verbose)

        if verbose:
            print "self.links_broken:", self.links_broken

        if importance:
            return self.get_importance_sampling_experiment_result(j - 1), self.links_broken
        else:
            return len(self.links_broken), self.links_broken

    def break_specified_links_in_order(self, links, verbose):

        self.links_broken = []

        all_host_pair_connected = self.check_all_host_pair_connected(verbose)

        for link in links:

            # Break the link
            self.links_broken.append((str(link[0]), str(link[1])))
            self.port_graph.remove_node_graph_link(link[0], link[1])
            all_host_pair_connected = self.check_all_host_pair_connected(verbose)

        # Restore the links for next run
        for link in self.links_broken:
            self.port_graph.add_node_graph_link(link[0], link[1], updating=True)
            all_host_pair_connected = self.check_all_host_pair_connected(verbose)

        if verbose:
            print "self.links_broken:", self.links_broken

        return self.links_broken