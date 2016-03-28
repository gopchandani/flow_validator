__author__ = 'Rakesh Kumar'

import sys
sys.path.append("./")

import math
import random

from itertools import permutations

from analysis.flow_validator import FlowValidator

class MonteCarloAnalysis(FlowValidator):

    def __init__(self, network_graph):
        super(MonteCarloAnalysis, self).__init__(network_graph)

        self.links_broken = []
        self.all_links = list(self.network_graph.get_switch_link_data())
        self.links_causing_disconnect = []
        self.links_not_causing_disconnect = []

        # Contains for each step (link failure), the alpha that was considered in computation
        self.alpha = []

        # Contains for each step (link failure), the size of set of links causing disconnect
        self.F = []

        # Contains for each step (link failure), the size of set of links not causing disconnect
        self.F_bar = []

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
        self.all_links = list(self.network_graph.get_switch_link_data())

        links_to_classify = list(set(self.all_links) - set(self.links_broken))

        # Go through every switch-switch link
        for ld in links_to_classify:

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

            if verbose:
                print "Causes Disconnect:", ld.causes_disconnect

        if verbose:
            print "links_not_causing_disconnect:"
            for ld in self.links_not_causing_disconnect:
                print ld

            print "links_causing_disconnect: "
            for ld in self.links_causing_disconnect:
                print ld

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
                    if verbose:
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

    def get_alpha(self, u, b, j, verbose=False):

        # if self.F_bar[j -1] > 0:
        #     return self.F[j - 1] / (self.N - j + 1)
        # else:
        #     return 1.0

        if b != None:

            beta = None

            if j == b + 1:
                beta = ((b + 1)/(u)) * ((self.F[b])/(self.N - b))
            elif j > b + 1:
                p = 1.0
                for i in xrange(0, j-2 + 1):
                    p = p * ((self.F_bar[i]) / ((1 - self.alpha[i+1]) * (self.N - i)))

                beta = (j/u) * ((self.F[j-1]) / (self.N - j + 1)) * (p)

            if verbose:
                print "beta:", beta

            # If beta is in the sensible range
            if beta > 0 or beta < 1.0:
                if self.F_bar[j - 1] > 0:
                    alpha = beta
                else:
                    alpha = 1.0
            elif beta >= 1.0:
                if self.F_bar[j -1] > 0:
                    alpha = self.F[j - 1] / (self.N - j + 1)
                else:
                    alpha = 1.0
            else:
                raise Exception("Weird beta, u: " + str(u) + " beta: " + str(beta))
        else:
            alpha = 0.0

        if verbose:
            print "alpha:", alpha

        return alpha

    def sample_link_uniform(self):

        # Construct where to sample from
        sample_from = list(set(self.all_links) - set(self.links_broken))

        # Randomly sample a link to break
        sampled_ld = random.choice(sample_from)

        return sampled_ld

    def sample_link_skewed(self, alpha):

        # Flip a coin
        unif = random.uniform(0, 1)

        if unif < alpha:
            sampled_ld = random.choice(self.links_causing_disconnect)
        else:
            sampled_ld = random.choice(self.links_not_causing_disconnect)

        if sampled_ld in self.links_broken:
            raise("Something wrong is happening with skewed link sampling")

        return sampled_ld

    def get_importance_sampling_experiment_result(self, k):
        result = 0.0
        
        prod = 1.0
        
        for i in xrange(0, k-2+1):
            
            first_factor = (self.F_bar[i]) / ((1 - self.alpha[i+1]) * (self.N - i))
            prod = prod * first_factor

        second_factor = (self.F[k-1]) / ((self.alpha[k]) * (self.N - k + 1))

        result = k * prod * second_factor

        return result

    def break_random_links_until_any_pair_disconnected_importance(self, u, verbose=False):
        self.links_broken = []
        self.alpha = []
        self.F = []
        self.F_bar = []

        # Check to see current state of affairs before doing anything for this step
        all_host_pair_connected = self.check_all_host_pair_connected(verbose)
        self.initialize_per_link_traffic_paths()
        self.classify_network_graph_links(verbose)
        self.F.append(len(self.links_causing_disconnect))
        self.F_bar.append(len(self.links_not_causing_disconnect))

        j = 0
        b = None
        if self.F[j] > 0:
            b = j

        self.alpha.append(self.get_alpha(u, b, j, False))

        while all_host_pair_connected:

            # Increment step index
            j += 1

            # Get a value of alpha for this step
            self.alpha.append(self.get_alpha(u, b, j, False))

            # Do a skewed sample using alpha:
            sampled_ld = self.sample_link_skewed(self.alpha[j])

            if verbose:
                print "Breaking the link:", sampled_ld

            # Break the link
            self.links_broken.append(sampled_ld)
            self.port_graph.remove_node_graph_link(sampled_ld.forward_link[0], sampled_ld.forward_link[1])

            # Check to see current state of affairs before doing anything for next step
            all_host_pair_connected = self.check_all_host_pair_connected(verbose)
            self.initialize_per_link_traffic_paths()
            self.classify_network_graph_links(verbose)
            self.F.append(len(self.links_causing_disconnect))
            self.F_bar.append(len(self.links_not_causing_disconnect))

            # b is the smallest index j, for which self.F[j] > 0
            if b == None:
                if self.F[j] > 0:
                    b = j

        # Restore the links for next run
        for link in self.links_broken:
            if verbose:
                print "Restoring the link:", link

            self.port_graph.add_node_graph_link(link.forward_link[0], link.forward_link[1], updating=True)

        self.classify_network_graph_links(verbose)

        result = self.get_importance_sampling_experiment_result(len(self.links_broken))

        return result, self.links_broken

    def try_breaking_permutation(self, p):
        self.links_broken = []

        for ld in p:
            self.links_broken.append(ld)
            self.port_graph.remove_node_graph_link(ld.forward_link[0], ld.forward_link[1])
            all_host_pair_connected = self.check_all_host_pair_connected(verbose=False)

            if not all_host_pair_connected:
                break

        # Restore the links for next run
        for link in self.links_broken:
            self.port_graph.add_node_graph_link(link.forward_link[0], link.forward_link[1], updating=True)

        return self.links_broken

    def compute_e_nf_exhaustive(self):

        # Checks for a prefix list, whether the given permutation matches any of them
        def matching_prefix(p, prefixes):
            matching_prefix = None

            for prefix in prefixes:

                this_prefix_matches = True
                for i in range(len(prefix)):
                    if prefix[i] != p[i]:
                        this_prefix_matches = False
                        break

                if this_prefix_matches:
                    matching_prefix = prefix
                    break

            return matching_prefix

        e_nf = 0.0

        broken_prefixes = []

        total_link_permutations = math.factorial(len(self.all_links))
        each_permutation_proability = 1.0 / total_link_permutations

        p_num = 0

        for p in permutations(self.all_links):
            p_num += 1

            if p_num % 10 == 0:
                print p_num, "/", total_link_permutations


            # If a prefix of this permutation has already been known to cause a failure, bolt
            matching_previous_prefix = matching_prefix(p, broken_prefixes)
            if matching_previous_prefix:
                e_nf += len(matching_previous_prefix)
                continue

            links_broken = self.try_breaking_permutation(p)

            e_nf += len(links_broken)

            if len(links_broken) < len(self.all_links):
                broken_prefixes.append(links_broken)

        e_nf *= each_permutation_proability

        print "e_nf:", e_nf

        return e_nf

    def break_random_links_until_any_pair_disconnected(self, verbose=False):

        self.links_broken = []

        # Check to see current state of affairs before doing anything for this step
        all_host_pair_connected = self.check_all_host_pair_connected(verbose)

        while all_host_pair_connected:

            sampled_link = self.sample_link_uniform()

            if verbose:
                print "Breaking the link:", sampled_link

            # Break the link
            self.links_broken.append(sampled_link)
            self.port_graph.remove_node_graph_link(sampled_link.forward_link[0], sampled_link.forward_link[1])

            # Check to see current state of affairs before doing anything for next step
            all_host_pair_connected = self.check_all_host_pair_connected(verbose)

        # Restore the links for next run
        for link in self.links_broken:
            if verbose:
                print "Restoring the link:", link
            self.port_graph.add_node_graph_link(link.forward_link[0], link.forward_link[1], updating=True)

        return len(self.links_broken), self.links_broken


    def generate_link_permutation(self):

        pool = tuple(self.all_links)
        n = len(pool)

        # Book-keeping arrays

        # Indices of the original collection which are delivered as the output
        indices = range(n)

        # Number of cycles left at a given index
        cycles = range(n, 0, -1)


        print indices
        # First permutation is same as the original collection
        yield tuple(pool[i] for i in indices[:n])

        while n:
            for i in reversed(range(n)):
                cycles[i] -= 1
                if cycles[i] == 0:
                    indices[i:] = indices[i+1:] + indices[i:i+1]
                    cycles[i] = n - i
                else:
                    j = cycles[i]
                    indices[i], indices[-j] = indices[-j], indices[i]
                    print indices
                    yield tuple(pool[i] for i in indices[:n])
                    break
            else:
                return

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

    def test_classification_breaking_specified_link_sequence(self, link_sequence, verbose):

        for link in link_sequence:

            # Break the link
            self.links_broken.append((str(link[0]), str(link[1])))
            self.port_graph.remove_node_graph_link(link[0], link[1])
            all_host_pair_connected = self.check_all_host_pair_connected(verbose)

        # Restore the links for next run
        for link in self.links_broken:
            self.port_graph.add_node_graph_link(link[0], link[1], updating=True)
            all_host_pair_connected = self.check_all_host_pair_connected(verbose)
