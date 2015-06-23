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

    def init_switch_port_graph(self):

        # Add a node per table in the port graph
        for flow_table in self.flow_tables:

            tp = Port(self,
                      port_type="table",
                      port_id=self.get_table_port_id(self.node_id, flow_table.table_id))

            self.add_port(tp)
            flow_table.port = tp

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

            incoming_port_match = Traffic(init_wildcard=True)
            incoming_port_match.set_field("in_port", int(port))

            self.add_edge(in_p,
                          self.flow_tables[0].port,
                          None,
                          incoming_port_match,
                          None,
                          None)

        # Try passing a wildcard through the flow table
        for flow_table in self.flow_tables:
            flow_table.init_flow_table_port_graph()

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
                 edge_action,
                 edge_filter_match,
                 applied_modifications,
                 written_modifications,
                 output_action_type=None):

        edge_data = self.g.get_edge_data(port1.port_id, port2.port_id)

        if edge_data:
            edge_data["edge_data"].add_edge_data((edge_filter_match,
                                                 edge_action,
                                                 applied_modifications,
                                                 written_modifications,
                                                 output_action_type))
        else:
            edge_data = EdgeData(port1, port2)
            edge_data.add_edge_data((edge_filter_match,
                                    edge_action,
                                    applied_modifications,
                                    written_modifications,
                                    output_action_type))

            self.g.add_edge(port1.port_id, port2.port_id, edge_data=edge_data)

        # Take care of any changes that need to be made to the predecessors of port1
        # due to addition of this edge

        #TODO: See how this is affected in cases involving rule addition
        #self.update_port_transfer_traffic(port1)

        return (port1.port_id, port2.port_id, edge_action)

    def remove_edge(self, port1, port2):

        # Remove the port-graph edges corresponding to ports themselves
        self.g.remove_edge(port1.port_id, port2.port_id)

        #TODO: See how this is affected in cases involving rule removal
        #self.update_port_transfer_traffic(port1)

    def compute_switch_transfer_traffic(self):

        # Inject wildcard traffic at each ingress port of the switch
        for port in self.ports:

            out_p_id = self.get_outgoing_port_id(self.node_id, port)
            out_p = self.get_port(out_p_id)

            transfer_traffic = Traffic(init_wildcard=True)
            transfer_traffic.set_port(out_p)
            out_p.transfer_traffic[out_p_id] = transfer_traffic

            self.compute_port_transfer_traffic(out_p, out_p.transfer_traffic[out_p_id], out_p)

    def account_port_transfer_traffic(self, port, traffic, dst_port):

        if dst_port.port_id not in port.transfer_traffic:
            port.transfer_traffic[dst_port.port_id] = traffic
        else:
            port.transfer_traffic[dst_port.port_id].union(traffic)

    def compute_port_transfer_traffic(self, curr, curr_transfer_traffic, dst_port):

        #print "Current Port:", curr.port_id, "Preds:", self.g.predecessors(curr.port_id), "dst:", dst_port.port_id
        self.account_port_transfer_traffic(curr, curr_transfer_traffic, dst_port)

        # Recursively call myself at each of my predecessors in the port graph
        for pred_id in self.g.predecessors_iter(curr.port_id):

            pred = self.get_port(pred_id)
            edge_data = self.g.get_edge_data(pred.port_id, curr.port_id)["edge_data"]
            pred_transfer_traffic = self.compute_edge_transfer_traffic(curr.transfer_traffic[dst_port.port_id], edge_data)
            pred_transfer_traffic.set_port(pred)

            # Base case: No traffic left to propagate to predecessors
            if not pred_transfer_traffic.is_empty():
                self.compute_port_transfer_traffic(pred, pred_transfer_traffic, dst_port)

    def compute_edge_transfer_traffic(self, curr_transfer_traffic, edge_data):

        pred_transfer_traffic = Traffic()

        for edge_filter_match, edge_action, applied_modifications, written_modifications, output_action_type \
                in edge_data.edge_data_list:

            if edge_action:
                if not edge_action.is_active:
                    continue

            if edge_data.edge_type == "egress":
                curr_transfer_traffic.set_field("in_port", is_wildcard=True)

                for te in curr_transfer_traffic.traffic_elements:
                    te.output_action_type = output_action_type

            if applied_modifications:
                ctt = curr_transfer_traffic.get_orig_traffic(applied_modifications)
            else:
                ctt = curr_transfer_traffic

            if edge_data.edge_type == "ingress":
                ctt = curr_transfer_traffic.get_orig_traffic()
            else:
                # At all the non-ingress edges accumulate written modifications
                # But these are useless if the output_action_type is applied.
                if written_modifications:
                    for te in ctt.traffic_elements:
                        te.written_modifications.update(written_modifications)

            i = edge_filter_match.intersect(ctt)

            if not i.is_empty():
                pred_transfer_traffic.union(i)

        return pred_transfer_traffic

    def update_port_transfer_traffic(self, node):

        node_preds = self.g.predecessors(node.port_id)

        # But this could have fail-over consequences for this port's predecessors' traffic elements
        for pred_id in node_preds:
            pred = self.get_port(pred_id)
            edge_data = self.g.get_edge_data(pred_id, node.port_id)["edge_data"]

            for edge_filter_match, edge_action, applied_modifications, written_modifications, output_action_type \
                    in edge_data.edge_data_list:

                if edge_action:
                    edge_action.perform_edge_failover()

            # But now the transfer_traffic on this port and its dependents needs to be modified to reflect the reality
            #self.update_pred_transfer_traffic(pred)

    # def update_pred_transfer_traffic(self, curr):
    #
    #     # This needs to be done for each destination for which curr holds transfer_traffic
    #     for dst in curr.transfer_traffic:
    #
    #         # First compute what the transfer_traffic for this dst looks like right now after edge status changes...
    #         now_transfer_traffic = Traffic()
    #         successors = self.g.successors(curr.port_id)
    #         for succ_id in successors:
    #             succ = self.get_port(succ_id)
    #             edge_data = self.g.get_edge_data(curr.port_id, succ.port_id)["edge_data"]
    #             t = self.compute_edge_transfer_traffic(curr.transfer_traffic[dst], edge_data)
    #             t.set_port(curr)
    #             now_transfer_traffic.union(t)
    #
    #         curr.transfer_traffic[dst].pipe_welding(now_transfer_traffic)
