__author__ = 'Rakesh Kumar'

from port_graph import PortGraph
from switch_port_graph import SwitchPortGraph
from port_graph_edge import PortGraphEdge, NetworkPortGraphEdgeData
from traffic import Traffic


class NetworkPortGraph(PortGraph):

    def __init__(self, network_graph, report_active_state):

        super(NetworkPortGraph, self).__init__(network_graph, report_active_state)

    def get_edge_from_admitted_traffic(self, pred, succ, admitted_traffic, edge_sw=None):

        edge = PortGraphEdge(pred, succ)

        # If the edge filter became empty, reflect that.
        if admitted_traffic.is_empty():
            pass
        else:
            # Each traffic element has its own edge_data, because of how it might have
            # traveled through the switch and what modifications it may have accumulated
            for te in admitted_traffic.traffic_elements:
                t = Traffic()
                t.add_traffic_elements([te])

                traffic_paths = None
                if edge_sw:

                    # Check to see the exact path of this traffic through the switch
                    traffic_paths = edge_sw.port_graph.get_paths(pred, succ, t, [pred], [], [])

                    if len(traffic_paths) == 0:
                        traffic_paths = edge_sw.port_graph.get_paths(pred, succ, t, [pred], [], [])
                        raise Exception("Found traffic but no paths to back it up.")

                edge_data = NetworkPortGraphEdgeData(t, te.switch_modifications, traffic_paths)
                edge.add_edge_data(edge_data)

        return edge

    def add_switch_nodes(self, sw, port_numbers):

        # First grab the port objects from the sw's node graph and add them to port_graph's node graph
        for port in port_numbers:

            self.add_node(sw.ports[port].network_port_graph_egress_node)
            self.add_node(sw.ports[port].network_port_graph_ingress_node)

    def add_sw_transfer_function(self, sw):

        '''

        Add nodes to the port graph that belong to its ports that are not connected to hosts.
        Add edges from the switch port graph for the nodes that correspond to ports not connected to hosts

        :param sw: Switch concerned
        :return: None
        '''

        for port in sw.non_host_port_iter():
            self.add_node(port.network_port_graph_egress_node)
            self.add_node(port.network_port_graph_ingress_node)
            
        for src_port in sw.non_host_port_iter():
            for dst_port in sw.non_host_port_iter():
                pred = src_port.switch_port_graph_ingress_node
                succ = dst_port.switch_port_graph_egress_node

                at = sw.port_graph.get_admitted_traffic(pred, succ)

                if not at.is_empty():
                    edge_obj = self.get_edge_from_admitted_traffic(pred, succ, at, edge_sw=sw)
                    self.add_edge(pred, succ, edge_obj)

    def add_switch_edges(self, sw, port_numbers):

        # Add edges from all possible source/destination ports
        for src_port_number in port_numbers:

            pred = sw.port_graph.get_ingress_node(sw.node_id, src_port_number)

            for succ in pred.admitted_traffic:
                admitted_traffic = sw.port_graph.get_admitted_traffic(pred, succ)
                edge_obj = self.get_edge_from_admitted_traffic(pred, succ, admitted_traffic, edge_sw=sw)
                self.add_edge(pred, succ, edge_obj)

    def modify_switch_transfer_edges(self, sw, modified_switch_edges):

        for modified_edge in modified_switch_edges:

            pred = sw.port_graph.get_node(modified_edge[0])
            succ = sw.port_graph.get_node(modified_edge[1])

            # First remove the edge
            edge = self.get_edge(pred, succ)
            if edge:
                self.remove_edge(pred, succ)

            # Then, add the edge back by using the new transfer traffic now
            admitted_traffic = sw.port_graph.get_admitted_traffic(pred, succ)
            edge_obj = self.get_edge_from_admitted_traffic(pred, succ, admitted_traffic, edge_sw=sw)
            self.add_edge(pred, succ, edge_obj)

    def init_network_port_graph(self):

        # Iterate through switches and add the ports and relevant abstract analysis
        for sw in self.network_graph.get_switches():

            sw.port_graph = SwitchPortGraph(sw.network_graph, sw, self.report_active_state)
            sw.port_graph.init_switch_port_graph()
            sw.port_graph.init_switch_admitted_traffic()

            self.add_sw_transfer_function(sw)

        # Add edges between ports on node edges, where nodes are only switches.
        for node_edge in self.network_graph.graph.edges():
            if not node_edge[0].startswith("h") and not node_edge[1].startswith("h"):
                self.add_node_graph_link(node_edge[0], node_edge[1])

    def de_init_network_port_graph(self):

        # Then get rid of the edges in the port graph
        for node_edge in self.network_graph.graph.edges():
            if not node_edge[0].startswith("h") and not node_edge[1].startswith("h"):
                self.remove_node_graph_link(node_edge[0], node_edge[1])

        # Then de-initialize switch port graph
        for sw in self.network_graph.get_switches():
            sw.port_graph.de_init_switch_port_graph()

    def init_network_admitted_traffic(self):

        # Go to each switch and find the ports that connects to other switches
        for sw in self.network_graph.get_switches():
            for non_host_port in sw.non_host_port_iter():

                # Accumulate traffic that is admitted for each host
                admitted_host_traffic = Traffic()
                for host_port in sw.host_port_iter():
                    at = sw.port_graph.get_admitted_traffic(non_host_port.switch_port_graph_ingress_node,
                                                            host_port.switch_port_graph_egress_node)
                    admitted_host_traffic.union(at)

                end_to_end_modified_edges = []
                self.propagate_admitted_traffic(non_host_port.network_port_graph_ingress_node,
                                                admitted_host_traffic,
                                                None,
                                                non_host_port.network_port_graph_ingress_node,
                                                end_to_end_modified_edges)

                admitted_host_traffic.set_field("in_port", int(non_host_port.port_number))

    def add_node_graph_link(self, node1_id, node2_id, updating=False):

        # Update the physical port representations in network graph objects
        edge_port_dict = self.network_graph.get_link_ports_dict(node1_id, node2_id)
        sw1 = self.network_graph.get_node_object(node1_id)
        sw2 = self.network_graph.get_node_object(node2_id)
        sw1.ports[edge_port_dict[node1_id]].state = "up"
        sw2.ports[edge_port_dict[node2_id]].state = "up"

        edge1 = (sw1.ports[edge_port_dict[node1_id]].switch_port_graph_egress_node,
                 sw2.ports[edge_port_dict[node2_id]].switch_port_graph_ingress_node)

        edge_obj = self.get_edge_from_admitted_traffic(edge1[0], edge1[1], Traffic(init_wildcard=True))
        self.add_edge(edge1[0], edge1[1], edge_obj)

        edge2 = (sw2.ports[edge_port_dict[node2_id]].switch_port_graph_egress_node,
                 sw1.ports[edge_port_dict[node1_id]].switch_port_graph_ingress_node)

        edge_obj = self.get_edge_from_admitted_traffic(edge2[0], edge2[1], Traffic(init_wildcard=True))
        self.add_edge(edge2[0], edge2[1], edge_obj)

        # Update transfer and admitted traffic
        if updating:

            end_to_end_modified_edges = []

            # Update admitted traffic due to link failure
            edge1 = (sw1.ports[edge_port_dict[node1_id]].network_port_graph_egress_node.node_id,
                     sw2.ports[edge_port_dict[node2_id]].network_port_graph_ingress_node.node_id)

            edge2 = (sw2.ports[edge_port_dict[node2_id]].network_port_graph_egress_node.node_id,
                     sw1.ports[edge_port_dict[node1_id]].network_port_graph_ingress_node.node_id)

            self.update_admitted_traffic([edge1, edge2], end_to_end_modified_edges)

            # Update admitted traffic due to switch transfer function changes
            modified_switch_edges = sw1.port_graph.update_admitted_traffic_due_to_port_state_change(edge_port_dict[node1_id],
                                                                                                    "port_up")
            modified_switch_edges = self.filter_modified_edges(modified_switch_edges)

            self.modify_switch_transfer_edges(sw1, modified_switch_edges)
            self.update_admitted_traffic(modified_switch_edges, end_to_end_modified_edges)

            modified_switch_edges = sw2.port_graph.update_admitted_traffic_due_to_port_state_change(edge_port_dict[node2_id],
                                                                                                    "port_up")
            modified_switch_edges = self.filter_modified_edges(modified_switch_edges)

            self.modify_switch_transfer_edges(sw2, modified_switch_edges)
            self.update_admitted_traffic(modified_switch_edges, end_to_end_modified_edges)

    def filter_modified_edges(self, modified_switch_edges):
        modified_switch_edges_new = []
        for modified_edge in modified_switch_edges:
            pred = self.get_node(modified_edge[0])
            succ = self.get_node(modified_edge[1])
            if pred and succ:
                modified_switch_edges_new.append(modified_edge)
        return modified_switch_edges_new

    def remove_node_graph_link(self, node1_id, node2_id):

        # Update the physical port representations in network graph objects
        edge_port_dict = self.network_graph.get_link_ports_dict(node1_id, node2_id)
        sw1 = self.network_graph.get_node_object(node1_id)
        sw2 = self.network_graph.get_node_object(node2_id)
        sw1.ports[edge_port_dict[node1_id]].state = "down"
        sw2.ports[edge_port_dict[node2_id]].state = "down"

        # Update port graph edge filters corresponding to the physical link
        edge1 = (sw1.ports[edge_port_dict[node1_id]].network_port_graph_egress_node,
                 sw2.ports[edge_port_dict[node2_id]].network_port_graph_ingress_node)

        self.remove_edge(*edge1)
        edge_obj = self.get_edge_from_admitted_traffic(edge1[0], edge1[1], Traffic(init_wildcard=False))
        self.add_edge(edge1[0], edge1[1], edge_obj)

        edge2 = (sw2.ports[edge_port_dict[node2_id]].network_port_graph_egress_node,
                 sw1.ports[edge_port_dict[node1_id]].network_port_graph_ingress_node)

        self.remove_edge(*edge2)
        edge_obj = self.get_edge_from_admitted_traffic(edge2[0], edge2[1], Traffic(init_wildcard=False))
        self.add_edge(edge2[0], edge2[1], edge_obj)

        end_to_end_modified_edges = []

        # Update admitted traffic due to link failure
        edge1 = (sw1.ports[edge_port_dict[node1_id]].network_port_graph_egress_node.node_id,
                 sw2.ports[edge_port_dict[node2_id]].network_port_graph_ingress_node.node_id)

        edge2 = (sw2.ports[edge_port_dict[node2_id]].network_port_graph_egress_node.node_id,
                 sw1.ports[edge_port_dict[node1_id]].network_port_graph_ingress_node.node_id)

        self.update_admitted_traffic([edge1, edge2], end_to_end_modified_edges)

        # Update admitted traffic due to switch transfer function changes
        modified_switch_edges = sw1.port_graph.update_admitted_traffic_due_to_port_state_change(edge_port_dict[node1_id], "port_down")
        modified_switch_edges = self.filter_modified_edges(modified_switch_edges)

        self.modify_switch_transfer_edges(sw1, modified_switch_edges)
        self.update_admitted_traffic(modified_switch_edges, end_to_end_modified_edges)

        modified_switch_edges = sw2.port_graph.update_admitted_traffic_due_to_port_state_change(edge_port_dict[node2_id], "port_down")
        modified_switch_edges = self.filter_modified_edges(modified_switch_edges)

        self.modify_switch_transfer_edges(sw2, modified_switch_edges)
        self.update_admitted_traffic(modified_switch_edges, end_to_end_modified_edges)

    def compute_edge_admitted_traffic(self, traffic_to_propagate, edge):

        pred_admitted_traffic = Traffic()

        for ed in edge.edge_data_list:

            # At succ edges, set the in_port of the admitted match for destination to wildcard
            if edge.edge_type == "outside":
                traffic_to_propagate.set_field("in_port", is_wildcard=True)
                traffic_to_propagate.clear_switch_modifications()

            # If there were modifications along the way...
            if ed.applied_modifications:
                ttp = traffic_to_propagate.get_orig_traffic(ed.applied_modifications)
            else:
                ttp = traffic_to_propagate

            i = ed.edge_filter_traffic.intersect(ttp)
            i.set_enabling_edge_data(ed)

            if not i.is_empty():
                pred_admitted_traffic.union(i)

        return pred_admitted_traffic

    def get_succs_with_admitted_traffic_and_vuln_rank(self, pred, failed_succ, at, vuln_rank, dst):

        succs_traffic = []

        # If the dst is from the same switch where this at dst goes, take the successors that go there as candidates
        possible_succs = set()
        for at_dst_node in pred.admitted_traffic:
            if at_dst_node.sw == dst.sw:
                possible_succs.update(pred.admitted_traffic[at_dst_node].keys())

        for succ in possible_succs:

            if succ == failed_succ:
                continue

            # First check if the successor would carry this traffic at all
            enabling_edge_data_list = []

            from analysis.util import get_admitted_traffic_via_succ
            at_dst_succ = get_admitted_traffic_via_succ(self, pred, succ, dst)

            # For traffic going from ingress->egress node on any switch, set the ingress traffic
            # of specific traffic to simulate that the traffic would arrive on that port.
            if pred.node_type == "ingress" and succ.node_type == "egress":
                at.set_field("in_port", int(pred.parent_obj.port_number))

            # Check to see if the successor would carry some of the traffic from here
            succ_int = at.intersect(at_dst_succ)
            if not succ_int.is_empty():
                enabling_edge_data_list = succ_int.get_enabling_edge_data()
            else:
                # Do not go further if there is no traffic admitted via this succ
                pass

            traffic_at_succ = succ_int.get_modified_traffic()

            # If so, make sure the traffic is carried because of edge_data with vuln_rank as specified
            if enabling_edge_data_list:

                vuln_rank_check = True

                # TODO: This may cause problem with duplicates (i.e. two edge data with exact same
                # traffic carried but with different vuln_ranks)

                for ed in enabling_edge_data_list:
                    if ed.get_vuln_rank() != vuln_rank:
                        vuln_rank_check = False

                if vuln_rank_check:
                    succs_traffic.append((succ, traffic_at_succ))

        if not succs_traffic:
            print "No alternative successors."

        return succs_traffic

    # Returns if the given link fails, the path would have an alternative way to get around
    def get_backup_ingress_nodes_and_traffic(self, path, ld):

        backup_ingress_nodes_and_traffic = []

        # Find the path_edges that get affected by the failure of given link
        for i in range(0, len(path.path_edges)):
            edge, enabling_edge_data, traffic_at_pred = path.path_edges[i]
            edge_tuple = (edge[0].node_id, edge[1].node_id)

            if edge_tuple == ld.forward_port_graph_edge or edge_tuple == ld.reverse_port_graph_edge:

                # Go to the switch and ask if a backup edge exists in the transfer function
                #  for the traffic carried by this path at that link

                p_edge, p_enabling_edge_data, p_traffic_at_pred = path.path_edges[i - 1]
                backup_succs = self.get_succs_with_admitted_traffic_and_vuln_rank(p_edge[0],
                                                                                  p_edge[1],
                                                                                  p_traffic_at_pred,
                                                                                  1,
                                                                                  path.dst_node)

                # TODO: Compute the ingress node from successor (Assumption, there is always one succ on egress node)
                for succ, succ_traffic in backup_succs:
                    ingress_node = list(self.successors_iter(succ))[0]

                    # Avoid adding as possible successor if it is for the link that has failed
                    # This can happen for 'reversing' paths
                    if not (ingress_node.node_id == ld.forward_port_graph_edge[1] or
                                    ingress_node.node_id == ld.reverse_port_graph_edge[1]):
                        backup_ingress_nodes_and_traffic.append((ingress_node, succ_traffic))

        # If so, return the ingress node on the next switch, where that edge leads to
        return backup_ingress_nodes_and_traffic

    def link_failure_causes_path_disconnect(self, path, ld):

        causes_disconnect = False
        backup_ingress_nodes_and_traffic = self.get_backup_ingress_nodes_and_traffic(path, ld)

        # If there is no backup successors, ld failure causes disconnect
        if not backup_ingress_nodes_and_traffic:
            causes_disconnect = True

        # If there are backup successors, but they are not adequately carrying traffic, failure causes disconnect
        else:
            for ingress_node, traffic_to_carry in backup_ingress_nodes_and_traffic:

                # First get what is admitted at this node
                from analysis.util import get_admitted_traffic
                ingress_at = get_admitted_traffic(self, ingress_node.parent_obj, path.dst_node.parent_obj)

                # The check if it carries the required traffic
                if not ingress_at.is_subset_traffic(traffic_to_carry):
                    causes_disconnect = True
                    break

        return causes_disconnect
