__author__ = 'Rakesh Kumar'

from port_graph import PortGraph
from switch_port_graph import SwitchPortGraph
from port_graph_edge import PortGraphEdge, NetworkPortGraphEdgeData
from traffic import Traffic
from experiments.timer import Timer


class NetworkPortGraph(PortGraph):

    def __init__(self, network_graph):

        super(NetworkPortGraph, self).__init__(network_graph)

    def get_edge_from_admitted_traffic(self, pred, succ, admitted_traffic, edge_sw=None, exclude_inactive=False):

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
                        raise Exception("Found traffic but no paths to back it up.")
                    else:
                        # IF asked to exclude in-active...
                        # As long as there a single active path and carries the te, then we are good,
                        # otherwise, continue
                        if exclude_inactive:
                            active_path = False
                            for p in traffic_paths:
                                if p.get_max_active_rank() == 0:
                                    active_path = True
                                    break

                            if not active_path:
                                continue

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

        sw.port_graph = SwitchPortGraph(sw.network_graph, sw)
        sw.port_graph.init_switch_port_graph()
        sw.port_graph.init_switch_admitted_traffic()

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

        with Timer(verbose=True) as t:
            # Iterate through switches and add the ports and relevant abstract analysis
            for sw in self.network_graph.get_switches():
                self.add_sw_transfer_function(sw)

        print "Switch transfer functions added, took:", t.secs, "seconds."

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

    def init_network_admitted_traffic_for_sw(self, sw):
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

    def init_network_admitted_traffic(self):

        with Timer(verbose=True) as t:

            # Go to each switch and find the ports that connects to other switches
            for sw in self.network_graph.get_switches():
                self.init_network_admitted_traffic_for_sw(sw)

        print "Network admitted traffic initialized, took:", t.secs, "seconds."

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