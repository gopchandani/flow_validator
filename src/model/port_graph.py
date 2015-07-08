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

            for dst_p in src_p.transfer_traffic:

                # Don't add looping edges
                if src_p.port_number == dst_p.port_number:
                    continue

                sw.print_paths(src_p, dst_p, src_p.port_id)

                traffic_filter = src_p.transfer_traffic[dst_p]
                total_traffic = Traffic()
                for succ in traffic_filter:
                    total_traffic.union(traffic_filter[succ])
                self.add_edge(src_p, dst_p, total_traffic)

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

    def add_edge(self, src_port, dst_port, edge_filter_traffic):

        edge_data = EdgeData(src_port, dst_port)

        # Each traffic element has its own edge_data, because of how it might have
        # traveled through the switch and what modifications it may have accumulated
        for te in edge_filter_traffic.traffic_elements:
            t = Traffic()
            t.add_traffic_elements([te])
            edge_data.add_edge_data((t, te.switch_modifications))

        self.g.add_edge(src_port.port_id, dst_port.port_id, edge_data=edge_data)

        #self.update_switch_transfer_function(src_port.sw, src_port)

    def remove_edge(self, src_port, dst_port):

        # Remove the port-graph edges corresponding to ports themselves
        self.g.remove_edge(src_port.port_id, dst_port.port_id)

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

        outgoing_port_1 = self.get_port(self.get_outgoing_port_id(node1_id, edge_port_dict[node1_id]))
        outgoing_port_2 = self.get_port(self.get_outgoing_port_id(node2_id, edge_port_dict[node2_id]))

        outgoing_port_1.sw.update_port_transfer_traffic(outgoing_port_1, "port_down")
        outgoing_port_2.sw.update_port_transfer_traffic(outgoing_port_2, "port_down")
        pass

    def compute_edge_admitted_traffic(self, curr_admitted_traffic, edge_data):

        pred_admitted_traffic = Traffic()

        for edge_filter_traffic, modifications in edge_data.edge_data_list:

            # At egress edges, set the in_port of the admitted match for destination to wildcard
            if edge_data.edge_type == "egress":
                curr_admitted_traffic.set_field("in_port", is_wildcard=True)

            # If there were modifications along the way...
            if modifications:
                cat = curr_admitted_traffic.get_orig_traffic(modifications)
            else:
                cat = curr_admitted_traffic

            i = edge_filter_traffic.intersect(cat)

            if not i.is_empty():
                pred_admitted_traffic.union(i)

        return pred_admitted_traffic

    def print_paths(self, src_p, dst_p, path_str=""):
        at = src_p.admitted_traffic[dst_p.port_id]

        for succ_p in at:
            if succ_p:
                self.print_paths(succ_p, dst_p, path_str + " -> " + succ_p.port_id)
            else:
                print path_str

    def account_port_admitted_traffic(self, port, propagating_traffic, succ, dst_port):

        traffic_to_propagate = None
        curr_succ_dst_traffic = None

        # If the traffic at this port already exist for this dst-succ combination,
        # Grab it, compute delta with what is being propagated and fill up the gaps
        try:
            curr_succ_dst_traffic = port.admitted_traffic[dst_port.port_id][succ]
            traffic_to_propagate = curr_succ_dst_traffic.difference(propagating_traffic)
            port.admitted_traffic[dst_port.port_id][succ].union(traffic_to_propagate)

        # If there is no traffic for this dst-succ combination prior to this propagation
        # Setup a traffic object, store it and propagate it no need to compute any delta.
        except KeyError:
            port.admitted_traffic[dst_port.port_id][succ] = Traffic()
            port.admitted_traffic[dst_port.port_id][succ].union(propagating_traffic)
            traffic_to_propagate = propagating_traffic

        return traffic_to_propagate

    def compute_admitted_traffic(self, curr, propagating_traffic, succ, dst_port):

        #print "Current Port:", curr.port_id, "Preds:", self.g.predecessors(curr.port_id), "dst:", dst_port.port_id

        traffic_to_propagate = self.account_port_admitted_traffic(curr, propagating_traffic, succ, dst_port)

        if not traffic_to_propagate.is_empty():

            # Recursively call myself at each of my predecessors in the port graph
            for pred_id in self.g.predecessors_iter(curr.port_id):

                pred = self.get_port(pred_id)
                edge_data = self.g.get_edge_data(pred.port_id, curr.port_id)["edge_data"]
                pred_admitted_traffic = self.compute_edge_admitted_traffic(traffic_to_propagate, edge_data)

                # Base case: No traffic left to propagate to predecessors
                if not pred_admitted_traffic.is_empty():
                    self.compute_admitted_traffic(pred, pred_admitted_traffic, curr, dst_port)