__author__ = 'Rakesh Kumar'

import networkx as nx

from collections import defaultdict
from traffic import Traffic
from port import Port
from edge_data import EdgeData

class Switch():

    def __init__(self, sw_id, network_graph):

        self.g = nx.DiGraph()
        self.node_id = sw_id
        self.network_graph = network_graph
        self.flow_tables = []
        self.group_table = None
        self.ports = None

        # Synthesis stuff
        self.intents = defaultdict(dict)
        self.synthesis_tag = int(self.node_id[1:])

        # Analysis stuff
        self.in_port_match = None
        self.accepted_destination_match = {}

        self.port_graph = None

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

    def add_edge(self,
                 port1,
                 port2,
                 edge_causing_flow,
                 edge_action,
                 edge_filter_match,
                 applied_modifications,
                 written_modifications,
                 output_action_type=None):

        edge_data = self.g.get_edge_data(port1.port_id, port2.port_id)

        if edge_data:
            edge_data["edge_data"].add_edge_data(edge_filter_match,
                                                 edge_causing_flow,
                                                 edge_action,
                                                 applied_modifications,
                                                 written_modifications,
                                                 output_action_type)
        else:
            edge_data = EdgeData(port1, port2)
            edge_data.add_edge_data(edge_filter_match,
                                    edge_causing_flow,
                                    edge_action,
                                    applied_modifications,
                                    written_modifications,
                                    output_action_type)

            self.g.add_edge(port1.port_id, port2.port_id, edge_data=edge_data)

        # Take care of any changes that need to be made to the predecessors of port1
        # due to addition of this edge
        self.update_predecessors(port1)

        return (port1.port_id, port2.port_id, edge_action)

    def remove_edge(self, port1, port2):

        # Remove the port-graph edges corresponding to ports themselves
        self.g.remove_edge(port1.port_id, port2.port_id)

        self.update_predecessors(port1)

    def update_predecessors(self, node):

        node_preds = self.g.predecessors(node.port_id)

        # But this could have fail-over consequences for this port's predecessors' match elements
        for pred_id in node_preds:
            pred = self.get_port(pred_id)
            edge_data = self.g.get_edge_data(pred_id, node.port_id)["edge_data"]

            for edge_filter_match, edge_causing_flow, edge_action, \
                applied_modifications, written_modifications, output_action_type in edge_data.edge_data_list:
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

    def init_switch_port_graph(self, port_graph):

        self.port_graph = port_graph

        # Add a node per table in the port graph
        for flow_table in self.flow_tables:

            tp = Port(self,
                      port_type="table",
                      port_id=self.get_table_port_id(self.node_id, flow_table.table_id))

            self.add_port(tp)
            flow_table.port = tp
            flow_table.port_graph = self.port_graph

        # Add two nodes per physical port in port graph one for incoming and outgoing direction
        # Connect incoming direction port to table 0's port
        for port in self.ports:

            in_p = Port(self,
                        port_type="ingress",
                        port_id=self.get_incoming_port_id(self.node_id, port))

            out_p = Port(self,
                         port_type="egress",
                         port_id=self.get_outgoing_port_id(self.node_id, port))

            in_p.state = "up"
            out_p.state = "up"

            in_p.port_number = int(port)
            out_p.port_number = int(port)

            self.add_port(in_p)
            self.add_port(out_p)

            self.port_graph.add_port(in_p)
            self.port_graph.add_port(out_p)

            incoming_port_match = Traffic(init_wildcard=True)
            incoming_port_match.set_field("in_port", int(port))

            self.add_edge(in_p,
                                     self.flow_tables[0].port,
                                     None,
                                     None,
                                     incoming_port_match,
                                     None,
                                     None)

        # Try passing a wildcard through the flow table
        for flow_table in self.flow_tables:
            flow_table.init_flow_table_port_graph()

    def compute_transfer_function(self):

        # Inject wildcard traffic at each ingress port of the switch
        for port in self.ports:

            out_p_id = self.get_outgoing_port_id(self.node_id, port)
            out_p = self.get_port(out_p_id)

            transfer_traffic = Traffic(init_wildcard=True)
            transfer_traffic.set_port(out_p)
            out_p.transfer_traffic[out_p_id] = transfer_traffic

            self.compute_transfer_traffic(out_p, out_p.transfer_traffic[out_p_id], out_p)

        # Add relevant edges to the port graph
        for port in self.ports:

            in_p_id = self.get_incoming_port_id(self.node_id, port)
            in_p = self.port_graph.get_port(in_p_id)

            for out_p_id in in_p.transfer_traffic:
                out_p = self.port_graph.get_port(out_p_id)

                # Don't add looping edges
                if in_p.port_number == out_p.port_number:
                    continue

                traffic_filter = in_p.transfer_traffic[out_p_id]
                self.port_graph.add_edge(in_p, out_p, traffic_filter)

    def compute_transfer_traffic(self, curr, curr_transfer_traffic, dst_port):

       # print "Current Port:", curr.port_id, "Preds:", self.port_graph.g.predecessors(curr.port_id)

        if dst_port.port_id not in curr.transfer_traffic:
            curr.transfer_traffic[dst_port.port_id] = curr_transfer_traffic
        else:
            curr.transfer_traffic[dst_port.port_id].union(curr_transfer_traffic)

        # Recursively call myself at each of my predecessors in the port graph
        for pred_id in self.g.predecessors_iter(curr.port_id):

            pred = self.get_port(pred_id)
            pred_transfer_traffic = self.compute_pred_transfer_traffic(pred, curr, dst_port.port_id)

            # Base cases
            # 1. No traffic left to propagate to predecessors
            # 2. There is some traffic but current port is ingress
            if not pred_transfer_traffic.is_empty() and  curr.port_type != "ingress":
                self.compute_transfer_traffic(pred, pred_transfer_traffic, dst_port)

    def compute_pred_transfer_traffic(self, pred, curr, dst_port_id):

        pred_transfer_traffic = Traffic()
        edge_data = self.g.get_edge_data(pred.port_id, curr.port_id)["edge_data"]

        for edge_filter_match, \
            edge_causing_flow, \
            edge_action, \
            applied_modifications, \
            written_modifications, \
            output_action_type in edge_data.edge_data_list:

            if edge_action:
                if not edge_action.is_active:
                    continue

            if dst_port_id in curr.transfer_traffic:

                if edge_data.edge_type == "egress":
                    curr.transfer_traffic[dst_port_id].set_field("in_port", is_wildcard=True)

                    for te in curr.transfer_traffic[dst_port_id].traffic_elements:
                        te.output_action_type = output_action_type

                if applied_modifications:
                    curr_transfer_traffic = curr.transfer_traffic[dst_port_id].get_orig_traffic(applied_modifications)
                    for te in curr_transfer_traffic.traffic_elements:
                        te.applied_modifications.update(applied_modifications)
                else:
                    curr_transfer_traffic = curr.transfer_traffic[dst_port_id]

                if edge_data.edge_type == "ingress":
                    curr_transfer_traffic = curr_transfer_traffic.get_orig_traffic()
                else:
                    if written_modifications:
                        for te in curr_transfer_traffic.traffic_elements:
                            te.written_modifications.update(written_modifications)

                i = edge_filter_match.intersect(curr_transfer_traffic)

                if not i.is_empty():
                    i.set_port(pred)
                    pred_transfer_traffic.union(i)

        return pred_transfer_traffic

    def de_init_switch_port_graph(self):

        # Try passing a wildcard through the flow table
        for flow_table in self.flow_tables:
            flow_table.de_init_flow_table_port_graph()

        # Remove nodes for physical ports
        for port in self.ports:

            in_p = self.get_port(self.get_incoming_port_id(self.node_id, port))
            out_p = self.get_port(self.get_outgoing_port_id(self.node_id, port))

            self.remove_edge(in_p, self.flow_tables[0].port)

            self.remove_port(in_p)
            self.remove_port(out_p)

            del in_p
            del out_p

        # Remove table ports
        # Add a node per table in the port graph
        for flow_table in self.flow_tables:

            tp = self.get_port(self.get_table_port_id(self.node_id, flow_table.table_id))
            self.remove_port(tp)
            flow_table.port = None
            flow_table.port_graph = None
            del tp
