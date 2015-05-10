__author__ = 'Rakesh Kumar'

import gc

import networkx as nx
from port import Port
from traffic import Traffic
from network_graph import NetworkGraph

class PortGraph:

    def __init__(self, network_graph):

        self.network_graph = network_graph
        self.g = nx.MultiDiGraph()

    def get_table_port_id(self, switch_id, table_number):
        return switch_id + ":table" + str(table_number)

    def get_incoming_port_id(self, node_id, port_number):
        return node_id + ":ingress" + str(port_number)

    def get_outgoing_port_id(self, node_id, port_number):
        return node_id + ":egress" + str(port_number)

    def add_port(self, port):
        self.g.add_node(port.port_id, p=port)

    def remove_port(self, port):
        self.g.remove_node(port.port_id)

    def get_port(self, port_id):
        return self.g.node[port_id]["p"]

    def init_port_graph(self):

        #Add a port for controller
        self.init_global_controller_port()

        # Iterate through switches and add the ports and relevant abstract analysis
        for sw in self.network_graph.get_switches():
            sw.init_switch_port_graph(self)

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

    def add_edge(self, port1, port2, key, edge_filter_match):

        edge_type = None
        if port1.port_type == "table" and port2.port_type == "egress":
            edge_type = "egress"
        elif port1.port_type == "ingress" and port2.port_type == "table":
            edge_type = "ingress"

        e = (port1.port_id, port2.port_id, key)

        self.g.add_edge(*e,
                        edge_filter_match=edge_filter_match,
                        edge_type=edge_type)

        # Take care of any changes that need to be made to the predecessors of port1
        # due to addition of this edge
        self.update_predecessors(port1)

        return e

    def remove_edge(self, port1, port2):

        # Remove the port-graph edges corresponding to ports themselves
        self.g.remove_edge(port1.port_id, port2.port_id)

        self.update_predecessors(port1)

    def update_predecessors(self, node):

        node_preds = self.g.predecessors(node.port_id)
        #print "update_predecessors node_preds:", node_preds

        # But this could have fail-over consequences for this port's predecessors' match elements
        for pred_id in node_preds:
            pred = self.get_port(pred_id)
            edge_data = self.g.get_edge_data(pred_id, node.port_id)

            edge_data_keys = edge_data.keys()
            for flow, edge_action in edge_data_keys:
                if flow:
                    flow.update_port_graph_edges()

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

        edge_data = self.network_graph.get_edge_port_dict(node1_id, node2_id)

        from_port = self.get_port(self.get_outgoing_port_id(node1_id, edge_data[node1_id]))
        to_port = self.get_port(self.get_incoming_port_id(node2_id, edge_data[node2_id]))
        from_port.state = "up"
        to_port.state = "up"
        self.add_edge(from_port, to_port, (None, None), Traffic(init_wildcard=True))

        from_port = self.get_port(self.get_outgoing_port_id(node2_id, edge_data[node2_id]))
        to_port = self.get_port(self.get_incoming_port_id(node1_id, edge_data[node1_id]))
        from_port.state = "up"
        to_port.state = "up"
        self.add_edge(from_port, to_port, (None, None), Traffic(init_wildcard=True))

    def remove_node_graph_edge(self, node1_id, node2_id):

        edge_data = self.network_graph.get_edge_port_dict(node1_id, node2_id)

        from_port = self.get_port(self.get_outgoing_port_id(node1_id, edge_data[node1_id]))
        to_port = self.get_port(self.get_incoming_port_id(node2_id, edge_data[node2_id]))
        from_port.state = "down"
        to_port.state = "down"
        self.remove_edge(from_port, to_port)

        from_port = self.get_port(self.get_outgoing_port_id(node2_id, edge_data[node2_id]))
        to_port = self.get_port(self.get_incoming_port_id(node1_id, edge_data[node1_id]))
        from_port.state = "down"
        to_port.state = "down"
        self.remove_edge(from_port, to_port)

    def compute_pred_admitted_traffic(self, pred, curr, dst_port_id):

        pred_admitted_traffic = Traffic()
        edge_data = self.g.get_edge_data(pred.port_id, curr.port_id)

        for flow, edge_action in edge_data:
            this_edge = edge_data[(flow, edge_action)]

            if edge_action:
                if not edge_action.is_active:
                    continue

            if dst_port_id in curr.admitted_traffic:

                # At egress edges, set the in_port of the admitted match for destination to wildcard
                if this_edge["edge_type"] == "egress":
                    curr.admitted_traffic[dst_port_id].set_field("in_port", is_wildcard=True)

                # This check takes care of any applied actions
                if flow and flow.applied_field_modifications:
                    curr_admitted_traffic = \
                        curr.admitted_traffic[dst_port_id].get_orig_traffic(flow.applied_field_modifications)
                else:
                    curr_admitted_traffic = curr.admitted_traffic[dst_port_id]

                # At ingress edge compute the effect of written-actions
                if this_edge["edge_type"] == "ingress":
                    curr_admitted_traffic = curr_admitted_traffic.get_orig_traffic()

                i = this_edge["edge_filter_match"].intersect(curr_admitted_traffic)
                if not i.is_empty():

                    # For non-ingress edges, accumulate written_field_modifications in the pred_admitted_traffic
                    if not this_edge["edge_type"] == "ingress" and flow and flow.written_field_modifications:

                        # Accumulate modifications
                        for me in i.match_elements:
                            me.written_field_modifications.update(flow.written_field_modifications)

                    i.set_port(pred)
                    pred_admitted_traffic.union(i)

        return pred_admitted_traffic

    # curr in this function below represents the port we assumed to have already reached
    # and are either collecting goods and stopping or recursively trying to get to its predecessors

    def compute_admitted_traffic(self, curr, curr_admitted_traffic, dst_port):

        #print "Current Port:", curr.port_id, "Preds:", self.g.predecessors(curr.port_id)

        # If curr has not seen destination at all, first get the curr_admitted_traffic account started
        if dst_port.port_id not in curr.admitted_traffic:
            curr.admitted_traffic[dst_port.port_id] = curr_admitted_traffic

        # If you already know something about this destination, then keep accumulating
        # this is for cases when recursion comes from multiple directions and accumulates here
        else:
            curr.admitted_traffic[dst_port.port_id].union(curr_admitted_traffic)

        # Implicit Base case: Host Ingress Ports better not have any predecessor
        # Recursively call myself at each of my predecessors in the port graph
        for pred_id in self.g.predecessors_iter(curr.port_id):

            pred = self.get_port(pred_id)
            pred_admitted_traffic = self.compute_pred_admitted_traffic(pred, curr, dst_port.port_id)

            if not pred_admitted_traffic.is_empty():
                self.compute_admitted_traffic(pred, pred_admitted_traffic, dst_port)
