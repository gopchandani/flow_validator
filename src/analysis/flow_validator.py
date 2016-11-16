import sys
import itertools
import numpy as np

sys.path.append("./")

from collections import defaultdict
from model.network_port_graph import NetworkPortGraph
from experiments.timer import Timer
from util import get_specific_traffic
from util import get_admitted_traffic, get_paths

__author__ = 'Rakesh Kumar'


class FlowValidator(object):

    def __init__(self, network_graph, report_active_state=True):
        self.network_graph = network_graph
        self.port_graph = NetworkPortGraph(network_graph, report_active_state, new_mode=True)

    def init_network_port_graph(self):
        self.port_graph.init_network_port_graph()
        self.port_graph.init_network_admitted_traffic()

    def de_init_network_port_graph(self):
        self.port_graph.de_init_network_port_graph()

    def initialize_per_link_traffic_paths(self, verbose=False):

        for ld in self.network_graph.get_switch_link_data():
            ld.traffic_paths = []

        for src_h_id in self.network_graph.host_ids:
            for dst_h_id in self.network_graph.host_ids:

                if src_h_id == dst_h_id:
                    continue

                src_host_obj = self.network_graph.get_node_object(src_h_id)
                dst_host_obj = self.network_graph.get_node_object(dst_h_id)

                specific_traffic = get_specific_traffic(self.network_graph, src_h_id, dst_h_id)

                all_paths = get_paths(self.port_graph,
                                        specific_traffic,
                                        src_host_obj.switch_port,
                                        dst_host_obj.switch_port)

                for path in all_paths:
                    if verbose:
                        print "src_h_id:", src_h_id, "dst_h_id:", dst_h_id, "path:", path

                    path_links = path.get_path_links()
                    for ld in path_links:

                        # Avoid adding the same path twice for cases when a link is repeated
                        if path not in ld.traffic_paths:
                            ld.traffic_paths.append(path)

    def port_pair_iter(self, src_zone, dst_zone):

        for src_port in src_zone:
            for dst_port in dst_zone:

                if src_port == dst_port:
                    continue

                # Doing validation only between ports that have hosts attached with them
                if not src_port.attached_host or not dst_port.attached_host:
                    continue

                yield src_port, dst_port

    def is_node_in_zone(self, node, zone, as_ingress_egress):

        result = False

        for port in zone:

            if as_ingress_egress == "ingress":
                if port.network_port_graph_ingress_node == node:
                    result = True
                    break

            elif as_ingress_egress == "egress":

                if port.network_port_graph_egress_node == node:
                    result = True
                    break
            else:
                raise Exception("Unknown as_ingress_egress")

        return result

    def are_zones_connected(self, src_zone, dst_zone, traffic):

        is_connected = True

        for src_port, dst_port in self.port_pair_iter(src_zone, dst_zone):

            # Setup the appropriate filter
            traffic.set_field("ethernet_source", int(src_port.attached_host.mac_addr.replace(":", ""), 16))
            traffic.set_field("ethernet_destination", int(dst_port.attached_host.mac_addr.replace(":", ""), 16))
            #traffic.set_field("vlan_id", src_port.sw.synthesis_tag + 0x1000, is_exception_value=True)
            #traffic.set_field("has_vlan_tag", 0)
            traffic.set_field("in_port", int(src_port.port_number))

            at = get_admitted_traffic(self.port_graph, src_port, dst_port)

            if not at.is_empty():
                if at.is_subset_traffic(traffic):
                    is_connected = True
                    #print all_paths[0]
                else:
                    print "src_port:", src_port, "dst_port:", dst_port, "at does not pass specific_traffic check."
                    is_connected = False
            else:
                # print "src_port:", src_port, "dst_port:", dst_port, "at is empty."
                is_connected = False

            if not is_connected:
                break

        return is_connected

    def are_zone_paths_within_limit(self, src_zone, dst_zone, traffic, l):

        within_limit = True

        for src_port, dst_port in self.port_pair_iter(src_zone, dst_zone):

            # Setup the appropriate filter
            traffic.set_field("ethernet_source", int(src_port.attached_host.mac_addr.replace(":", ""), 16))
            traffic.set_field("ethernet_destination", int(dst_port.attached_host.mac_addr.replace(":", ""), 16))
            traffic.set_field("vlan_id", src_port.sw.synthesis_tag + 0x1000, is_exception_value=True)
            traffic.set_field("in_port", int(src_port.port_number))

            traffic_paths = get_paths(self.port_graph, traffic, src_port, dst_port)

            for path in traffic_paths:
                if len(path) > l:
                    print "src_port:", src_port, "dst_port:", dst_port, "Path does not fit in specified limit:", path
                    within_limit = False
                    break

            if not within_limit:
                break

        return within_limit

    def are_zone_pair_exclusive(self, src_zone, dst_zone, traffic, el):
        is_exclusive = True

        self.initialize_per_link_traffic_paths()

        for l in el:

            # Check to see if the paths belonging to this link are all from src_zone to dst_zone
            for path in l.traffic_paths:

                if not self.is_node_in_zone(path.src_node, src_zone, "ingress") or \
                        not self.is_node_in_zone(path.dst_node, dst_zone, "egress"):

                    print "el:", el
                    print "Found path:", path
                    is_exclusive = False
                    break

            if not is_exclusive:
                break

        return is_exclusive

    def validate_zone_pair_connectivity(self, src_zone, dst_zone, traffic, k):

        is_connected = False

        if k == 0:
            is_connected = self.are_zones_connected(src_zone, dst_zone, traffic)
        else:
            for links_to_fail in itertools.permutations(list(self.network_graph.get_switch_link_data()), k):

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

    def validate_zone_pair_link_exclusivity(self, src_zone, dst_zone, traffic, el, k):
        is_exclusive = False

        if k == 0:
            is_exclusive = self.are_zone_pair_exclusive(src_zone, dst_zone, traffic, el)
        else:
            for links_to_fail in itertools.permutations(list(self.network_graph.get_switch_link_data()), k):

                for link in links_to_fail:
                    self.port_graph.remove_node_graph_link(link.forward_link[0], link.forward_link[1])

                is_exclusive = self.are_zone_pair_exclusive(src_zone, dst_zone, traffic, el)

                for link in links_to_fail:
                    self.port_graph.add_node_graph_link(link.forward_link[0], link.forward_link[1], updating=True)

                if not is_exclusive:
                    break

        return is_exclusive

    def validate_policy(self, policy_statement_list):

        # Keyed by src_port, dst_port, k
        validation_tuples = defaultdict(list)

        for ps in policy_statement_list:
            for i in range(ps.k+1):
                for src_port, dst_port in self.port_pair_iter(ps.src_zone, ps.dst_zone):
                    validation_tuples[(src_port, dst_port, i)].append((ps.traffic, ps.constraints))

        print validation_tuples

    def validate_zone_pair_connectivity_path_length_link_exclusivity(self, src_zone, dst_zone, traffic, l, el, k):

        is_connected = True
        within_limit = True
        is_exclusive = True

        incremental_times = []

        if k == 0:
            is_connected = self.are_zones_connected(src_zone, dst_zone, traffic)
            within_limit = self.are_zone_paths_within_limit(src_zone, dst_zone, traffic, l)
            is_exclusive = self.are_zone_pair_exclusive(src_zone, dst_zone, traffic, el)
        else:
            for links_to_fail in itertools.permutations(list(self.network_graph.get_switch_link_data()), k):

                for link in links_to_fail:

                    print "Failing:", link

                    with Timer(verbose=True) as t:
                        self.port_graph.remove_node_graph_link(link.forward_link[0], link.forward_link[1])
                    incremental_times.append(t.secs)

                if is_connected:
                    is_connected = self.are_zones_connected(src_zone, dst_zone, traffic)

                if within_limit:
                    within_limit = self.are_zone_paths_within_limit(src_zone, dst_zone, traffic, l)

                if is_exclusive:
                    is_exclusive = self.are_zone_pair_exclusive(src_zone, dst_zone, traffic, el)

                for link in links_to_fail:

                    print "Restoring:", link

                    with Timer(verbose=True) as t:
                        self.port_graph.add_node_graph_link(link.forward_link[0], link.forward_link[1], updating=True)
                    incremental_times.append(t.secs)

                # Break out of here if all three properties have been proven to be false
                if not is_connected and not within_limit and not is_exclusive:
                    break

        avg_incremental_time = np.mean(incremental_times)

        return is_connected, within_limit, is_exclusive, avg_incremental_time