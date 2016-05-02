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
                    traffic_paths = edge_sw.port_graph.get_paths(pred, succ, t, [pred], [], verbose=True)

                    if len(traffic_paths) == 0:
                        pass

                edge_data = NetworkPortGraphEdgeData(t, te.switch_modifications, traffic_paths)
                edge.add_edge_data(edge_data)

        return edge

    def add_switch_transfer_edges(self, sw):

        # First grab the port objects from the sw's node graph and add them to port_graph's node graph
        for port in sw.ports:

            self.add_node(sw.ports[port].network_port_graph_egress_node)
            self.add_node(sw.ports[port].network_port_graph_ingress_node)

        # Add edges from all possible source/destination ports
        for src_port_number in sw.ports:

            pred = sw.port_graph.get_ingress_node(sw.node_id, src_port_number)

            for succ in pred.admitted_traffic:
                admitted_traffic = sw.port_graph.get_admitted_traffic(pred, succ)
                edge = self.get_edge_from_admitted_traffic(pred, succ, admitted_traffic, edge_sw=sw)
                self.add_edge(pred, succ, edge)

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
            edge = self.get_edge_from_admitted_traffic(pred, succ, admitted_traffic, edge_sw=sw)
            self.add_edge(pred, succ, edge)

    def init_network_port_graph(self):

        # Iterate through switches and add the ports and relevant abstract analysis
        for sw in self.network_graph.get_switches():

            sw.port_graph = SwitchPortGraph(sw.network_graph, sw, self.report_active_state)
            sw.port_graph.init_switch_port_graph()
            sw.port_graph.compute_switch_admitted_traffic()
            # test_passed = sw.port_graph.test_one_port_failure_at_a_time(verbose=False)
            # print test_passed
            self.add_switch_transfer_edges(sw)
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

    def add_node_graph_link(self, node1_id, node2_id, updating=False):

        # Update the physical port representations in network graph objects
        edge_port_dict = self.network_graph.get_link_ports_dict(node1_id, node2_id)
        sw1 = self.network_graph.get_node_object(node1_id)
        sw2 = self.network_graph.get_node_object(node2_id)
        sw1.ports[edge_port_dict[node1_id]].state = "up"
        sw2.ports[edge_port_dict[node2_id]].state = "up"

        edge = self.get_edge_from_admitted_traffic(sw1.ports[edge_port_dict[node1_id]].switch_port_graph_egress_node,
                                                   sw2.ports[edge_port_dict[node2_id]].switch_port_graph_ingress_node,
                                                   Traffic(init_wildcard=True))

        self.add_edge(sw1.ports[edge_port_dict[node1_id]].network_port_graph_egress_node,
                      sw2.ports[edge_port_dict[node2_id]].network_port_graph_ingress_node,
                      edge)

        edge = self.get_edge_from_admitted_traffic(sw2.ports[edge_port_dict[node2_id]].switch_port_graph_egress_node,
                                                   sw1.ports[edge_port_dict[node1_id]].switch_port_graph_ingress_node,
                                                   Traffic(init_wildcard=True))

        self.add_edge(sw2.ports[edge_port_dict[node2_id]].network_port_graph_egress_node,
                      sw1.ports[edge_port_dict[node1_id]].network_port_graph_ingress_node,
                      edge)

        # Update transfer and admitted traffic
        if updating:

            end_to_end_modified_edges = []

            modified_switch_edges = sw1.port_graph.update_admitted_traffic_due_to_port_state_change(edge_port_dict[node1_id],
                                                                                         "port_up")
            self.modify_switch_transfer_edges(sw1, modified_switch_edges)
            self.update_admitted_traffic(modified_switch_edges, end_to_end_modified_edges)

            modified_switch_edges = sw2.port_graph.update_admitted_traffic_due_to_port_state_change(edge_port_dict[node2_id],
                                                                                         "port_up")
            self.modify_switch_transfer_edges(sw2, modified_switch_edges)
            self.update_admitted_traffic(modified_switch_edges, end_to_end_modified_edges)

    def remove_node_graph_link(self, node1_id, node2_id):

        # Update the physical port representations in network graph objects
        edge_port_dict = self.network_graph.get_link_ports_dict(node1_id, node2_id)
        sw1 = self.network_graph.get_node_object(node1_id)
        sw2 = self.network_graph.get_node_object(node2_id)
        sw1.ports[edge_port_dict[node1_id]].state = "down"
        sw2.ports[edge_port_dict[node2_id]].state = "down"

        # Update port graph
        self.remove_edge(sw1.ports[edge_port_dict[node1_id]].network_port_graph_egress_node,
                         sw2.ports[edge_port_dict[node2_id]].network_port_graph_ingress_node)

        self.remove_edge(sw2.ports[edge_port_dict[node2_id]].network_port_graph_egress_node,
                         sw1.ports[edge_port_dict[node1_id]].network_port_graph_ingress_node)

        end_to_end_modified_edges = []

        # Update transfer and admitted traffic
        modified_switch_edges = sw1.port_graph.update_admitted_traffic_due_to_port_state_change(edge_port_dict[node1_id], "port_down")
        self.modify_switch_transfer_edges(sw1, modified_switch_edges)
        self.update_admitted_traffic(modified_switch_edges, end_to_end_modified_edges)

        modified_switch_edges = sw2.port_graph.update_admitted_traffic_due_to_port_state_change(edge_port_dict[node2_id], "port_down")
        self.modify_switch_transfer_edges(sw2, modified_switch_edges)
        self.update_admitted_traffic(modified_switch_edges, end_to_end_modified_edges)

    def compute_edge_admitted_traffic(self, traffic_to_propagate, edge):

        pred_admitted_traffic = Traffic()

        for ed in edge.edge_data_list:

            # At succ edges, set the in_port of the admitted match for destination to wildcard
            if edge.edge_type == "outside":
                traffic_to_propagate.set_field("in_port", is_wildcard=True)

            # If there were modifications along the way...
            if ed.applied_modifications:
                # If the edge ports belong to the same switch, keep the modifications, otherwise get rid of them.
                if edge.port1.sw == edge.port2.sw:
                    ttp = traffic_to_propagate.get_orig_traffic(ed.applied_modifications, store_switch_modifications=True)
                else:
                    ttp = traffic_to_propagate.get_orig_traffic(ed.applied_modifications, store_switch_modifications=False)
            else:
                ttp = traffic_to_propagate

            i = ed.edge_filter_traffic.intersect(ttp)
            i.set_enabling_edge_data(ed)

            if not i.is_empty():
                pred_admitted_traffic.union(i)

        return pred_admitted_traffic