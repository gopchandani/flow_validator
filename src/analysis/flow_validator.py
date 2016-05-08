__author__ = 'Rakesh Kumar'

import sys
import itertools

sys.path.append("./")

from collections import defaultdict
from model.network_port_graph import NetworkPortGraph
from model.traffic import Traffic

class FlowValidator(object):

    def __init__(self, network_graph, report_active_state=True):
        self.network_graph = network_graph
        self.port_graph = NetworkPortGraph(network_graph, report_active_state)

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
                    print "src_h_id:", src_h_id,  "-> dst_h_id:", dst_h_id, "disconnected."
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

                self.validate_host_pair_backup(src_h_id, dst_h_id, verbose)

    def get_specific_traffic(self, src_h_id, dst_h_id):

        src_h_obj = self.network_graph.get_node_object(src_h_id)
        dst_h_obj = self.network_graph.get_node_object(dst_h_id)

        specific_traffic = Traffic(init_wildcard=True)
        specific_traffic.set_field("ethernet_type", 0x0800)
        specific_traffic.set_field("ethernet_source", int(src_h_obj.mac_addr.replace(":", ""), 16))
        specific_traffic.set_field("ethernet_destination", int(dst_h_obj.mac_addr.replace(":", ""), 16))
        specific_traffic.set_field("in_port", int(src_h_obj.switch_port_attached))
        specific_traffic.set_field("vlan_id", src_h_obj.switch_obj.synthesis_tag + 0x1000, is_exception_value=True)
        specific_traffic.set_field("has_vlan_tag", 0)

        return specific_traffic

    def port_pair_iter(self, src_zone, dst_zone):

        for src_port in src_zone:
            for dst_port in dst_zone:

                if src_port == dst_port:
                    continue

                # Doing validation only between ports that have hosts attached with them
                if not src_port.attached_host or not dst_port.attached_host:
                    continue

                yield src_port, dst_port

    def are_zones_connected(self, src_zone, dst_zone, traffic):

        is_connected = True

        for src_port, dst_port in self.port_pair_iter(src_zone, dst_zone):

            ingress_node = self.port_graph.get_ingress_node(src_port.sw.node_id, src_port.port_number)
            egress_node = self.port_graph.get_egress_node(dst_port.sw.node_id, dst_port.port_number)

            # Setup the appropriate filter
            traffic.set_field("ethernet_source", int(src_port.attached_host.mac_addr.replace(":", ""), 16))
            traffic.set_field("ethernet_destination", int(dst_port.attached_host.mac_addr.replace(":", ""), 16))
            traffic.set_field("vlan_id", src_port.sw.synthesis_tag + 0x1000, is_exception_value=True)
            traffic.set_field("has_vlan_tag", 0)
            traffic.set_field("in_port", int(src_port.port_number))

            at = self.port_graph.get_admitted_traffic(ingress_node, egress_node)

            all_paths = self.port_graph.get_paths(ingress_node,
                                                  egress_node,
                                                  traffic,
                                                  [ingress_node],
                                                  [],
                                                  True)

            if not at.is_empty():
                if at.is_subset_traffic(traffic):
                    is_connected = True
                    print all_paths[0]
                else:
                    print "src_port:", src_port, "dst_port:", dst_port, "at does not pass specific_traffic check."
                    is_connected = False
            else:
                print "src_port:", src_port, "dst_port:", dst_port, "at is empty."
                is_connected = False

            if not is_connected:
                break

        return is_connected

    def validate_zone_pair_connectivity(self, src_zone, dst_zone, traffic, k):

        is_connected = False

        if k == 0:
            is_connected = self.are_zones_connected(src_zone, dst_zone, traffic)
        else:
            for links_to_fail in itertools.permutations(list(self.network_graph.get_switch_link_data()), k):

                if not("s2" in links_to_fail[0].link_ports_dict and "s1" in links_to_fail[0].link_ports_dict):
                    continue

                for link in links_to_fail:
                    print "Failing:", link
                    self.port_graph.remove_node_graph_link(link.forward_link[0], link.forward_link[1])

                is_connected = self.are_zones_connected(src_zone, dst_zone, traffic)

                for link in links_to_fail:
                    print "Restoring:", link
                    self.port_graph.add_node_graph_link(link.forward_link[0], link.forward_link[1], updating=True)

                if not is_connected:
                    break

        return is_connected

    def are_zone_paths_within_limit(self, src_zone, dst_zone, traffic, l):

        within_limit = True

        for src_port, dst_port in self.port_pair_iter(src_zone, dst_zone):

            ingress_node = self.port_graph.get_ingress_node(src_port.sw.node_id, src_port.port_number)
            egress_node = self.port_graph.get_egress_node(dst_port.sw.node_id, dst_port.port_number)

            # Setup the appropriate filter
            traffic.set_field("ethernet_source", int(src_port.attached_host.mac_addr.replace(":", ""), 16))
            traffic.set_field("ethernet_destination", int(dst_port.attached_host.mac_addr.replace(":", ""), 16))
            traffic.set_field("vlan_id", src_port.sw.synthesis_tag + 0x1000, is_exception_value=True)
            traffic.set_field("in_port", int(src_port.port_number))

            traffic_paths = self.port_graph.get_paths(ingress_node,
                                                      egress_node,
                                                      traffic,
                                                      [ingress_node],
                                                      [], verbose=False)

            for path in traffic_paths:
                if len(path) > l:
                    print "src_port:", src_port, "dst_port:", dst_port, "Path:", path
                    within_limit = False
                    break

            if not within_limit:
                break

        return within_limit

    def validate_zone_pair_path_length(self, src_zone, dst_zone, traffic, l, k):
        within_limit = False

        if k == 0:
            within_limit = self.are_zone_paths_within_limit(src_zone, dst_zone, traffic, l)
        else:
            for links_to_fail in itertools.permutations(list(self.network_graph.get_switch_link_data()), k):

                for link in links_to_fail:
                    self.port_graph.remove_node_graph_link(link.forward_link[0], link.forward_link[1])

                within_limit = self.are_zone_paths_within_limit(src_zone, dst_zone, traffic, l)

                for link in links_to_fail:
                    self.port_graph.add_node_graph_link(link.forward_link[0], link.forward_link[1], updating=True)

                if not within_limit:
                    break

        return within_limit

    def are_zone_pair_exlusive(self, src_zone, dst_zone, traffic, el):
        is_exclusive = True

        self.initialize_per_link_traffic_paths()

        for src_port, dst_port in self.port_pair_iter(src_zone, dst_zone):

            ingress_node = self.port_graph.get_ingress_node(src_port.sw.node_id, src_port.port_number)
            egress_node = self.port_graph.get_egress_node(dst_port.sw.node_id, dst_port.port_number)

            for l in el:

                # Check to see if the paths belonging to this link are all for the source/destination pairs in all_paths
                for path in l.traffic_paths:

                    if not path.src_node == ingress_node or not path.dst_node == egress_node:
                        print "l:", l, "src_port:", src_port, "dst_port:", dst_port, "Path:", path
                        is_exclusive = False
                        break

                if not is_exclusive:
                    break

            if not is_exclusive:
                break

        return is_exclusive

    def validate_zone_pair_link_exclusivity(self, src_zone, dst_zone, traffic, el, k):
        is_exclusive = False

        if k == 0:
            is_exclusive = self.are_zone_pair_exlusive(src_zone, dst_zone, traffic, el)
        else:
            for links_to_fail in itertools.permutations(list(self.network_graph.get_switch_link_data()), k):

                for link in links_to_fail:
                    self.port_graph.remove_node_graph_link(link.forward_link[0], link.forward_link[1])

                is_exclusive = self.are_zone_pair_exlusive(src_zone, dst_zone, traffic, el)

                for link in links_to_fail:
                    self.port_graph.add_node_graph_link(link.forward_link[0], link.forward_link[1], updating=True)

                if not is_exclusive:
                    break

        return is_exclusive