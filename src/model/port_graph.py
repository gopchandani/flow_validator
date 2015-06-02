__author__ = 'Rakesh Kumar'

import networkx as nx
from port import Port
from edge_data import EdgeData
from traffic import Traffic

class PortGraph:

    def __init__(self, network_graph):

        self.network_graph = network_graph
        self.g = nx.DiGraph()
        self.g2 = nx.DiGraph()

    def get_table_port_id(self, switch_id, table_number):
        return switch_id + ":table" + str(table_number)

    def get_incoming_port_id(self, node_id, port_number):
        return node_id + ":ingress" + str(port_number)

    def get_outgoing_port_id(self, node_id, port_number):
        return node_id + ":egress" + str(port_number)

    def add_port(self, port):
        self.g.add_node(port.port_id, p=port)

    def add_port_2(self, port):
        self.g2.add_node(port.port_id, p=port)

    def remove_port(self, port):
        self.g.remove_node(port.port_id)

    def remove_port_2(self, port):
        self.g2.remove_node(port.port_id)

    def get_port(self, port_id):
        return self.g.node[port_id]["p"]

    def get_port_2(self, port_id):
        return self.g2.node[port_id]["p"]

    def init_port_graph(self):

        # Add a port for controller
        self.init_global_controller_port()

        # Iterate through switches and add the ports and relevant abstract analysis
        for sw in self.network_graph.get_switches():
            sw.init_switch_port_graph(self)
            sw.compute_transfer_function()

        # Add edges between ports on node edges, where nodes are only switches.
        for node_edge in self.network_graph.graph.edges():
            if not node_edge[0].startswith("h") and not node_edge[1].startswith("h"):
                self.add_node_graph_edge(node_edge[0], node_edge[1])

    def de_init_port_graph(self):

        # First get rid of the controller port
        self.de_init_controller_port()

        # Then get rid of the edges in the port graph
        for node_edge in self.network_graph.graph.edges():
            if not node_edge[0].startswith("h") and not node_edge[1].startswith("h"):
                self.remove_node_graph_edge(node_edge[0], node_edge[1])

        # Then de-initialize switch port graph
        for sw in self.network_graph.get_switches():
            sw.de_init_switch_port_graph(self)

    def add_edge(self,
                 port1,
                 port2,
                 edge_causing_flow,
                 edge_action,
                 edge_filter_match,
                 applied_modifications,
                 written_modifications):

        edge_data = self.g.get_edge_data(port1.port_id, port2.port_id)

        if edge_data:
            edge_data["edge_data"].add_edge_data(edge_filter_match, edge_causing_flow, edge_action,
                                                 applied_modifications, written_modifications)
        else:
            edge_data = EdgeData(port1, port2)
            edge_data.add_edge_data(edge_filter_match, edge_causing_flow, edge_action,
                                    applied_modifications, written_modifications)
            self.g.add_edge(port1.port_id, port2.port_id, edge_data=edge_data)

        # Take care of any changes that need to be made to the predecessors of port1
        # due to addition of this edge
        self.update_predecessors(port1)

        return (port1.port_id, port2.port_id, edge_action)

    def add_edge_2(self, port1, port2, edge_filter_traffic):

        edge_data = EdgeData(port1, port2)

        for te in edge_filter_traffic.traffic_elements:
            t = Traffic(te)
            t.add_traffic_elements([te])
            edge_data.add_edge_data_2(t, te.applied_modifications)

        self.g2.add_edge(port1.port_id, port2.port_id, edge_data=edge_data)

    def remove_edge(self, port1, port2):

        # Remove the port-graph edges corresponding to ports themselves
        self.g.remove_edge(port1.port_id, port2.port_id)

        self.update_predecessors(port1)

    def remove_edge_2(self, port1, port2):

        # Remove the port-graph edges corresponding to ports themselves
        self.g2.remove_edge(port1.port_id, port2.port_id)


    def update_predecessors(self, node):

        node_preds = self.g.predecessors(node.port_id)

        # But this could have fail-over consequences for this port's predecessors' match elements
        for pred_id in node_preds:
            pred = self.get_port(pred_id)
            edge_data = self.g.get_edge_data(pred_id, node.port_id)["edge_data"]

            for edge_filter_match, edge_causing_flow, edge_action, \
                applied_modifications, written_modifications in edge_data.edge_data_list:
                if edge_causing_flow:
                    edge_causing_flow.update_port_graph_edges()

            # But now the admitted_traffic on this port and its dependents needs to be modified to reflect the reality
            self.update_match_elements(pred)

    def update_match_elements(self, curr):

        #print "update_match_elements at port:", curr.port_id

        # This needs to be done for each destination for which curr holds admitted_traffic
        for dst in curr.admitted_traffic:

            #print "update_match_elements dst:", dst

            # First compute what the admitted_traffic for this dst looks like right now after edge status changes...
            now_admitted_traffic = Traffic()
            for succ_id in self.g.successors_iter(curr.port_id):
                succ = self.get_port(succ_id)
                now_admitted_traffic.union(self.compute_pred_admitted_traffic(curr, succ, dst))

            curr.admitted_traffic[dst].pipe_welding(now_admitted_traffic)


    def init_global_controller_port(self):
        cp = Port(None, port_type="controller", port_id="4294967293")
        self.add_port(cp)

    def de_init_controller_port(self):
        cp = self.get_port("4294967293")
        self.remove_port(cp)
        del cp

    def add_node_graph_edge(self, node1_id, node2_id):

        edge_port_dict = self.network_graph.get_edge_port_dict(node1_id, node2_id)

        from_port = self.get_port(self.get_outgoing_port_id(node1_id, edge_port_dict[node1_id]))
        to_port = self.get_port(self.get_incoming_port_id(node2_id, edge_port_dict[node2_id]))
        from_port.state = "up"
        to_port.state = "up"
        self.add_edge(from_port, to_port, None, None, Traffic(init_wildcard=True), None, None)
        self.add_edge_2(from_port, to_port, Traffic(init_wildcard=True))

        from_port = self.get_port(self.get_outgoing_port_id(node2_id, edge_port_dict[node2_id]))
        to_port = self.get_port(self.get_incoming_port_id(node1_id, edge_port_dict[node1_id]))
        from_port.state = "up"
        to_port.state = "up"
        self.add_edge(from_port, to_port, None, None, Traffic(init_wildcard=True), None, None)
        self.add_edge_2(from_port, to_port, Traffic(init_wildcard=True))

    def remove_node_graph_edge(self, node1_id, node2_id):

        edge_port_dict = self.network_graph.get_edge_port_dict(node1_id, node2_id)

        from_port = self.get_port(self.get_outgoing_port_id(node1_id, edge_port_dict[node1_id]))
        to_port = self.get_port(self.get_incoming_port_id(node2_id, edge_port_dict[node2_id]))
        from_port.state = "down"
        to_port.state = "down"
        self.remove_edge(from_port, to_port)
        self.remove_edge_2(from_port, to_port)

        from_port = self.get_port(self.get_outgoing_port_id(node2_id, edge_port_dict[node2_id]))
        to_port = self.get_port(self.get_incoming_port_id(node1_id, edge_port_dict[node1_id]))
        from_port.state = "down"
        to_port.state = "down"
        self.remove_edge(from_port, to_port)
        self.remove_edge_2(from_port, to_port)

    def compute_pred_admitted_traffic(self, pred, curr, dst_port_id):

        pred_admitted_traffic = Traffic()
        edge_data = self.g2.get_edge_data(pred.port_id, curr.port_id)["edge_data"]

        for edge_filter_traffic, modifications in edge_data.edge_data_list:

            if dst_port_id in curr.admitted_traffic:

                # At egress edges, set the in_port of the admitted match for destination to wildcard
                if edge_data.edge_type == "egress":
                    curr.admitted_traffic[dst_port_id].set_field("in_port", is_wildcard=True)

                # This check takes care of any applied actions
                if modifications:
                    curr_admitted_traffic = \
                        curr.admitted_traffic[dst_port_id].get_orig_traffic(modifications)
                else:
                    curr_admitted_traffic = curr.admitted_traffic[dst_port_id]

                i = edge_filter_traffic.intersect(curr_admitted_traffic)

                if not i.is_empty():
                    i.set_port(pred)
                    pred_admitted_traffic.union(i)

        return pred_admitted_traffic

    # curr in this function below represents the port we assumed to have already reached
    # and are either collecting goods and stopping or recursively trying to get to its predecessors

    def compute_admitted_traffic(self, curr, curr_admitted_traffic, dst_port):

        print "Current Port:", curr.port_id, "Preds:", self.g2.predecessors(curr.port_id)

        # If curr has not seen destination at all, first get the curr_admitted_traffic account started
        if dst_port.port_id not in curr.admitted_traffic:
            curr.admitted_traffic[dst_port.port_id] = curr_admitted_traffic

        # If you already know something about this destination, then keep accumulating
        # this is for cases when recursion comes from multiple directions and accumulates here
        else:
            curr.admitted_traffic[dst_port.port_id].union(curr_admitted_traffic)

        # Recursively call myself at each of my predecessors in the port graph
        for pred_id in self.g2.predecessors_iter(curr.port_id):

            pred = self.get_port(pred_id)
            pred_admitted_traffic = self.compute_pred_admitted_traffic(pred, curr, dst_port.port_id)

            if not pred_admitted_traffic.is_empty():
                self.compute_admitted_traffic(pred, pred_admitted_traffic, dst_port)