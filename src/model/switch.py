__author__ = 'Rakesh Kumar'

from collections import defaultdict
from traffic import Traffic
from port import Port


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

            incoming_port_match = Traffic(init_wildcard=True)
            incoming_port_match.set_field("in_port", int(port))

            self.port_graph.add_edge(in_p,
                                     self.flow_tables[0].port,
                                     (None, None),
                                     incoming_port_match)

        # Try passing a wildcard through the flow table
        for flow_table in self.flow_tables:
            flow_table.init_flow_table_port_graph()


    def compute_transfer_function(self):

        # Inject wildcard traffic at each ingress port of the switch
        for port in self.ports:

            out_p_id = self.port_graph.get_outgoing_port_id(self.node_id, port)
            out_p = self.port_graph.get_port(out_p_id)

            admitted_traffic = Traffic(init_wildcard=True)
            admitted_traffic.set_port(out_p)
            out_p.admitted_traffic[out_p_id] = admitted_traffic

            self.port_graph.compute_admitted_traffic(out_p, out_p.admitted_traffic[out_p_id], out_p)

        print "here"

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
