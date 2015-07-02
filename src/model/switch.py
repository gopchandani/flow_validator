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
        #self.update_port_transfer_traffic(port1)

        return (port1.port_id, port2.port_id, edge_action)

    def remove_edge(self, port1, port2):

        # Remove the port-graph edges corresponding to ports themselves
        self.g.remove_edge(port1.port_id, port2.port_id)

        #self.update_port_transfer_traffic(port1)

    def compute_switch_transfer_traffic(self):

        # Inject wildcard traffic at each ingress port of the switch
        for port in self.ports:

            out_p_id = self.get_outgoing_port_id(self.node_id, port)
            out_p = self.get_port(out_p_id)

            transfer_traffic = Traffic(init_wildcard=True)
            transfer_traffic.set_port(out_p)
            #out_p.transfer_traffic[out_p_id] = transfer_traffic

            self.compute_port_transfer_traffic(out_p, transfer_traffic, None, out_p)

    def print_paths(self, src_p, dst_p, path_str=""):
        tt = src_p.transfer_traffic[dst_p.port_id]

        for succ_p in tt:
            if succ_p:
                self.print_paths(succ_p, dst_p, path_str + " -> " + succ_p.port_id)
            else:
                print path_str

    def account_port_transfer_traffic(self, port, propagating_traffic, succ, dst_port):

        traffic_to_propagate = None
        curr_succ_dst_traffic = None

        # If the traffic at this port already exist for this dst-succ combination,
        # Grab it, compute delta with what is being propagated and fill up the gaps
        try:
            curr_succ_dst_traffic = port.transfer_traffic[dst_port.port_id][succ]
            traffic_to_propagate = curr_succ_dst_traffic.compute_diff_traffic(propagating_traffic)
            port.transfer_traffic[dst_port.port_id][succ].union(traffic_to_propagate)

        # If there is no traffic for this dst-succ combination prior to this propagation
        # Setup a traffic object, store it and propagate it no need to compute any delta.
        except KeyError:
            port.transfer_traffic[dst_port.port_id][succ] = Traffic()
            port.transfer_traffic[dst_port.port_id][succ].union(propagating_traffic)
            traffic_to_propagate = propagating_traffic

        return traffic_to_propagate

    def compute_port_transfer_traffic(self, curr, propagating_traffic, succ, dst_port):

        #print "Current Port:", curr.port_id, "Preds:", self.g.predecessors(curr.port_id), "dst:", dst_port.port_id

        traffic_to_propagate = self.account_port_transfer_traffic(curr, propagating_traffic, succ, dst_port)

        if not traffic_to_propagate.is_empty():

            # Recursively call myself at each of my predecessors in the port graph
            for pred_id in self.g.predecessors_iter(curr.port_id):

                pred = self.get_port(pred_id)
                edge_data = self.g.get_edge_data(pred.port_id, curr.port_id)["edge_data"]
                pred_transfer_traffic = self.compute_edge_transfer_traffic(traffic_to_propagate, edge_data)
                pred_transfer_traffic.set_port(pred)

                # Base case: No traffic left to propagate to predecessors
                if not pred_transfer_traffic.is_empty():
                    self.compute_port_transfer_traffic(pred, pred_transfer_traffic, curr, dst_port)

    def compute_edge_transfer_traffic(self, traffic_to_propagate, edge_data):

        pred_transfer_traffic = Traffic()

        for edge_filter_match, edge_action, applied_modifications, written_modifications, output_action_type \
                in edge_data.edge_data_list:

            if edge_action:
                if not edge_action.is_active:
                    continue

            if edge_data.edge_type == "egress":
                traffic_to_propagate.set_field("in_port", is_wildcard=True)

                for te in traffic_to_propagate.traffic_elements:
                    te.output_action_type = output_action_type

            if applied_modifications:
                ttp = traffic_to_propagate.get_orig_traffic(applied_modifications)
            else:
                ttp = traffic_to_propagate

            if edge_data.edge_type == "ingress":
                ttp = traffic_to_propagate.get_orig_traffic()
            else:
                # At all the non-ingress edges accumulate written modifications
                # But these are useless if the output_action_type is applied.
                if written_modifications:
                    for te in ttp.traffic_elements:
                        te.written_modifications.update(written_modifications)

            i = edge_filter_match.intersect(ttp)

            if not i.is_empty():
                pred_transfer_traffic.union(i)

        return pred_transfer_traffic


    # This one executes Step 1 and computes exactly what traffic it is (per-destination), that is being transferred
    # via this port after all the changes that have happened in the graph.
    # These changes can include:
    #  -- Addition/Removal of physical edges
    #  -- Addition/Removal of rules inside the table port

    def update_port_transfer_traffic(self, port, event_type):

        # The cardinal processing is per-destination
        for dst in port.transfer_traffic:

            # If a port goes down, go through all the Traffic from its predecessor ports and
            # 1. remove traffic that goes through this port
            # 2. perform edge_failover

            if event_type == "port_down":

                # Compute what traffic is being admitted here now
                total_traffic = Traffic()

                for pred_id in self.g.predecessors(port.port_id):
                    pred = self.get_port(pred_id)
                    edge_data = self.g.get_edge_data(pred_id, port.port_id)["edge_data"]
                    for edge_filter_match, edge_action, applied_modifications, written_modifications, output_action_type \
                            in edge_data.edge_data_list:

                        if edge_action:
                            edge_action.perform_edge_failover()

                    #  and propagate it to the predecessors
                    self.compute_port_transfer_traffic(pred, total_traffic, port, dst)

            elif event_type == "port_up":
                pass
