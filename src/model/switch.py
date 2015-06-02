__author__ = 'Rakesh Kumar'

from collections import defaultdict
from traffic import Traffic
from port import Port
from edge_data import EdgeData


class Switch():

    def __init__(self, sw_id, network_graph):

        self.node_id = sw_id
        self.network_graph = network_graph
        self.flow_tables = []
        self.group_table = None
        self.ports = None

        #Synthesis stuff
        self.intents = defaultdict(dict)
        self.synthesis_tag = int(self.node_id[1:])

        #Analysis stuff
        self.in_port_match = None
        self.accepted_destination_match = {}

        self.port_graph = None

    def init_switch_port_graph(self, port_graph):

        self.port_graph = port_graph

        # Add a node per table in the port graph
        for flow_table in self.flow_tables:

            tp = Port(self,
                      port_type="table",
                      port_id=self.port_graph.get_table_port_id(self.node_id, flow_table.table_id))

            self.port_graph.add_port(tp)
            flow_table.port = tp
            flow_table.port_graph = self.port_graph

        # Add two nodes per physical port in port graph one for incoming and outgoing direction
        # Connect incoming direction port to table 0's port
        for port in self.ports:

            in_p = Port(self,
                        port_type="ingress",
                        port_id=self.port_graph.get_incoming_port_id(self.node_id, port))

            out_p = Port(self,
                         port_type="egress",
                         port_id=self.port_graph.get_outgoing_port_id(self.node_id, port))

            in_p.state = "up"
            out_p.state = "up"

            in_p.port_number = int(port)
            out_p.port_number = int(port)

            self.port_graph.add_port(in_p)
            self.port_graph.add_port(out_p)

            self.port_graph.add_port_2(in_p)
            self.port_graph.add_port_2(out_p)

            incoming_port_match = Traffic(init_wildcard=True)
            incoming_port_match.set_field("in_port", int(port))

            self.port_graph.add_edge(in_p,
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

            out_p_id = self.port_graph.get_outgoing_port_id(self.node_id, port)
            out_p = self.port_graph.get_port(out_p_id)

            transfer_traffic = Traffic(init_wildcard=True)
            transfer_traffic.set_port(out_p)
            out_p.transfer_traffic[out_p_id] = transfer_traffic

            self.compute_transfer_traffic(out_p, out_p.transfer_traffic[out_p_id], out_p)

        # Add relevant edges to the port graph
        for port in self.ports:

            in_p_id = self.port_graph.get_incoming_port_id(self.node_id, port)
            in_p = self.port_graph.get_port_2(in_p_id)

            for out_p_id in in_p.transfer_traffic:
                out_p = self.port_graph.get_port_2(out_p_id)

                # Don't add looping edges
                if in_p.port_number == out_p.port_number:
                    continue

                traffic_filter = in_p.transfer_traffic[out_p_id]
                self.port_graph.add_edge_2(in_p, out_p, traffic_filter)

    def compute_transfer_traffic(self, curr, curr_transfer_traffic, dst_port):

       # print "Current Port:", curr.port_id, "Preds:", self.port_graph.g.predecessors(curr.port_id)

        if dst_port.port_id not in curr.transfer_traffic:
            curr.transfer_traffic[dst_port.port_id] = curr_transfer_traffic
        else:
            curr.transfer_traffic[dst_port.port_id].union(curr_transfer_traffic)

        # Recursively call myself at each of my predecessors in the port graph
        for pred_id in self.port_graph.g.predecessors_iter(curr.port_id):

            pred = self.port_graph.get_port(pred_id)
            pred_transfer_traffic = self.compute_pred_transfer_traffic(pred, curr, dst_port.port_id)

            # Base cases
            # 1. No traffic left to propagate to predecessors
            # 2. There is some traffic but current port is ingress
            if not pred_transfer_traffic.is_empty() and  curr.port_type != "ingress":
                self.compute_transfer_traffic(pred, pred_transfer_traffic, dst_port)

    def compute_pred_transfer_traffic(self, pred, curr, dst_port_id):

        pred_transfer_traffic = Traffic()
        edge_data = self.port_graph.g.get_edge_data(pred.port_id, curr.port_id)["edge_data"]

        for edge_filter_match, edge_causing_flow, edge_action, \
            applied_modifications, written_modifications in edge_data.edge_data_list:

            if edge_action:
                if not edge_action.is_active:
                    continue

            if dst_port_id in curr.transfer_traffic:

                if edge_data.edge_type == "egress":
                    curr.transfer_traffic[dst_port_id].set_field("in_port", is_wildcard=True)

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
                        for te in i.traffic_elements:
                            te.written_modifications.update(written_modifications)

                i = edge_filter_match.intersect(curr_transfer_traffic)

                if not i.is_empty():
                    i.set_port(pred)
                    pred_transfer_traffic.union(i)

        return pred_transfer_traffic

    def de_init_switch_port_graph(self, port_graph):

        # Try passing a wildcard through the flow table
        for flow_table in self.flow_tables:
            flow_table.de_init_flow_table_port_graph()

        # Remove nodes for physical ports
        for port in self.ports:

            in_p = self.port_graph.get_port(self.port_graph.get_incoming_port_id(self.node_id, port))
            out_p = self.port_graph.get_port(self.port_graph.get_outgoing_port_id(self.node_id, port))

            self.port_graph.remove_edge(in_p, self.flow_tables[0].port)

            self.port_graph.remove_port(in_p)
            self.port_graph.remove_port(out_p)

            del in_p
            del out_p

        # Remove table ports
        # Add a node per table in the port graph
        for flow_table in self.flow_tables:

            tp = self.port_graph.get_port(self.port_graph.get_table_port_id(self.node_id, flow_table.table_id))
            self.port_graph.remove_port(tp)
            flow_table.port = None
            flow_table.port_graph = None
            del tp
