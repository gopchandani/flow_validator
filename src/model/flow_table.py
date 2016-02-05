__author__ = 'Rakesh Kumar'

from port_graph_node import PortGraphNode
from match import Match
from traffic import Traffic, TrafficElement
from instruction_set import InstructionSet

from port_graph import get_table_node_id

class Flow():

    def __hash__(self):
        return hash(str(self.sw.node_id) + str(self.table_id) + str(id(self)))

    def __init__(self, sw, flow_json):

        self.sw = sw
        self.flow_json = flow_json
        self.network_graph = sw.network_graph
        self.written_actions = []
        self.applied_actions = []
        self.go_to_table = None

        if self.sw.network_graph.controller == "odl":
            self.table_id = self.flow_json["table_id"]
            self.priority = int(self.flow_json["priority"])
            self.match = Match(match_json=self.flow_json["match"], controller="odl", flow=self)

        elif self.sw.network_graph.controller == "ryu":
            self.table_id = self.flow_json["table_id"]
            self.priority = int(self.flow_json["priority"])
            self.match = Match(match_json=self.flow_json["match"], controller="ryu", flow=self)

        self.traffic_element = TrafficElement(init_match=self.match)
        self.traffic = Traffic()
        self.complement_traffic = Traffic()
        self.applied_traffic = None

        self.traffic.add_traffic_elements([self.traffic_element])
        self.complement_traffic.add_traffic_elements(self.traffic_element.get_complement_traffic_elements())

    def add_port_graph_edges(self):

        if not "instructions" in self.flow_json:
            print "Assuming this means to drop."
        else:
            if self.sw.network_graph.controller == "odl":
                self.instruction_set = InstructionSet(self.sw, self, self.flow_json["instructions"]["instruction"])

            elif self.sw.network_graph.controller == "ryu":
                self.instruction_set = InstructionSet(self.sw, self, self.flow_json["instructions"])

            self.applied_modifications = \
                self.instruction_set.applied_action_set.get_modified_fields_dict(self.traffic_element)

            self.written_modifications = \
                self.instruction_set.written_action_set.get_modified_fields_dict(self.traffic_element)

            port_graph_edges = self.instruction_set.applied_action_set.get_port_graph_edges()

            for out_port, output_action in port_graph_edges:

                output_action.instruction_type = "applied"
                egress_node = self.sw.get_egress_node(self.sw.node_id, out_port)

                e = self.sw.add_edge(self.sw.flow_tables[self.table_id].port_graph_node,
                                     egress_node,
                                     output_action,
                                     self.applied_traffic,
                                     self.applied_modifications,
                                     self.written_modifications)

            port_graph_edges = self.instruction_set.written_action_set.get_port_graph_edges()

            for out_port, output_action in port_graph_edges:

                output_action.instruction_type = "written"
                egress_node = self.sw.get_egress_node(self.sw.node_id, out_port)

                e = self.sw.add_edge(self.sw.flow_tables[self.table_id].port_graph_node,
                                     egress_node,
                                     output_action,
                                     self.applied_traffic,
                                     self.applied_modifications,
                                     self.written_modifications)

            # See the edge impact of any go-to-table instruction
            if self.instruction_set.goto_table:

                if self.instruction_set.goto_table < len(self.sw.flow_tables):
                    e = self.sw.add_edge(self.sw.flow_tables[self.table_id].port_graph_node,
                                         self.sw.flow_tables[self.instruction_set.goto_table].port_graph_node,
                                         None,
                                         self.applied_traffic,
                                         self.applied_modifications,
                                         self.written_modifications)
                else:
                    print "At switch:", self.sw.node_id, ", couldn't find flow table goto:", self.instruction_set.goto_table


class FlowTable():
    def __init__(self, sw, table_id, flow_list):

        self.sw = sw
        self.network_graph = sw.network_graph
        self.table_id = table_id
        self.flows = []

        self.port_graph_node = PortGraphNode(self.sw,
                                             get_table_node_id(self.sw.node_id, self.table_id),
                                             "table")

        for f in flow_list:
            f = Flow(sw, f)
            self.flows.append(f)

        #  Sort the flows list by priority
        self.flows = sorted(self.flows, key=lambda flow: flow.priority, reverse=True)

    def init_flow_table_port_graph(self):

        #print "flow_table:", self.table_id

        remaining_traffic = Traffic(init_wildcard=True)

        for flow in self.flows:

            #print "flow:", flow.flow_json

            intersection = flow.traffic.intersect(remaining_traffic)

            if not intersection.is_empty():

                # See what is left after this rule is through
                remaining_traffic = flow.complement_traffic.intersect(remaining_traffic)
                flow.applied_traffic = intersection

                # Add the edges in the portgraph
                flow.add_port_graph_edges()
            else:
                # Say that this flow does not matter
                flow.applied_traffic = None

    def de_init_flow_table_port_graph(self):
        pass