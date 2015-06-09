__author__ = 'Rakesh Kumar'

import networkx as nx
from port import Port
from edge_data import EdgeData
from traffic import Traffic

class PortGraph:

    def __init__(self, network_graph):

        self.network_graph = network_graph
        self.g = nx.DiGraph()

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

    def add_switch_transfer_function(self, sw):

        # First grab the port objects from the sw's node graph and add them to port_graph's node graph
        for port in sw.ports:
            self.add_port(sw.get_port(self.get_incoming_port_id(sw.node_id, port)))
            self.add_port(sw.get_port(self.get_outgoing_port_id(sw.node_id, port)))

        # Add edges from all possible source/destination ports
        for src_port_number in sw.ports:
            src_p = self.get_port(self.get_incoming_port_id(sw.node_id, src_port_number))

            for dst_p_id in src_p.transfer_traffic:
                dst_p = self.get_port(dst_p_id)

                # Don't add looping edges
                if src_p.port_number == dst_p.port_number:
                    continue

                traffic_filter = src_p.transfer_traffic[dst_p_id]
                self.add_edge(src_p, dst_p, traffic_filter)

    def init_port_graph(self):

        # Add a port for controller
        self.init_global_controller_port()

        # Iterate through switches and add the ports and relevant abstract analysis
        for sw in self.network_graph.get_switches():
            sw.init_switch_port_graph()
            sw.compute_switch_transfer_traffic()
            self.add_switch_transfer_function(sw)

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
            sw.de_init_switch_port_graph()

    def add_edge(self, port1, port2, edge_filter_traffic):

        edge_data = EdgeData(port1, port2)

        # Each traffic element has its own edge_data, because of how it might have
        # traveled through the switch and what modifications it may have accumulated

        for te in edge_filter_traffic.traffic_elements:
            t = Traffic()
            t.add_traffic_elements([te])
            edge_data.add_edge_data_2(t, te.effective_modifications)

        self.g.add_edge(port1.port_id, port2.port_id, edge_data=edge_data)

    def remove_edge(self, port1, port2):

        # Remove the port-graph edges corresponding to ports themselves
        self.g.remove_edge(port1.port_id, port2.port_id)

        port1.sw.update_port_transfer_traffic(port1)

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
        self.add_edge(from_port, to_port, Traffic(init_wildcard=True))

        from_port = self.get_port(self.get_outgoing_port_id(node2_id, edge_port_dict[node2_id]))
        to_port = self.get_port(self.get_incoming_port_id(node1_id, edge_port_dict[node1_id]))
        from_port.state = "up"
        to_port.state = "up"
        self.add_edge(from_port, to_port, Traffic(init_wildcard=True))

    def remove_node_graph_edge(self, node1_id, node2_id):

        edge_port_dict = self.network_graph.get_edge_port_dict(node1_id, node2_id)

        from_port = self.get_port(self.get_outgoing_port_id(node1_id, edge_port_dict[node1_id]))
        to_port = self.get_port(self.get_incoming_port_id(node2_id, edge_port_dict[node2_id]))
        from_port.state = "down"
        to_port.state = "down"
        self.remove_edge(from_port, to_port)

        from_port = self.get_port(self.get_outgoing_port_id(node2_id, edge_port_dict[node2_id]))
        to_port = self.get_port(self.get_incoming_port_id(node1_id, edge_port_dict[node1_id]))
        from_port.state = "down"
        to_port.state = "down"
        self.remove_edge(from_port, to_port)

    def compute_pred_admitted_traffic(self, pred, curr, dst_port_id):

        pred_admitted_traffic = Traffic()
        edge_data = self.g.get_edge_data(pred.port_id, curr.port_id)["edge_data"]

        for edge_filter_traffic, modifications in edge_data.edge_data_list:

            if dst_port_id in curr.admitted_traffic:

                # At egress edges, set the in_port of the admitted match for destination to wildcard
                if edge_data.edge_type == "egress":
                    curr.admitted_traffic[dst_port_id].set_field("in_port", is_wildcard=True)

                # If there were modifications along the way...
                if modifications:
                    curr_admitted_traffic = curr.admitted_traffic[dst_port_id].get_orig_traffic(modifications)
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

        #print "Current Port:", curr.port_id, "Preds:", self.g.predecessors(curr.port_id)

        # If curr has not seen destination at all, first get the curr_admitted_traffic account started
        if dst_port.port_id not in curr.admitted_traffic:
            curr.admitted_traffic[dst_port.port_id] = curr_admitted_traffic

        # If you already know something about this destination, then keep accumulating
        # this is for cases when recursion comes from multiple directions and accumulates here
        else:
            curr.admitted_traffic[dst_port.port_id].union(curr_admitted_traffic)

        # Recursively call myself at each of my predecessors in the port graph
        for pred_id in self.g.predecessors_iter(curr.port_id):

            pred = self.get_port(pred_id)
            pred_admitted_traffic = self.compute_pred_admitted_traffic(pred, curr, dst_port.port_id)

            if not pred_admitted_traffic.is_empty():
                self.compute_admitted_traffic(pred, pred_admitted_traffic, dst_port)