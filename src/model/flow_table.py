__author__ = 'Rakesh Kumar'

from match_element import MatchElement
from traffic import Traffic
from instruction_set import InstructionSet

class Flow():

    def __hash__(self):
        return hash(str(self.sw.node_id) + str(self.table_id) + str(id(self)))

    def __init__(self, sw, flow_json):

        self.sw = sw
        self.flow_json = flow_json
        self.network_graph = sw.network_graph
        self.port_graph = None
        self.written_actions = []
        self.applied_actions = []
        self.go_to_table = None

        self.applied_match = None
        self.port_graph_edges = []

        self.match = Traffic()
        self.complement_traffic = Traffic()

        if self.sw.network_graph.controller == "odl":
            self.parse_odl_flow()

        elif self.sw.network_graph.controller == "ryu":
            self.parse_ryu_flow()

        self.match.match_elements.append(self.match_element)
        complement_match_elements = self.match_element.get_complement_match_elements()
        self.complement_traffic.add_match_elements(complement_match_elements)

    def parse_odl_flow(self):

        self.table_id = self.flow_json["table_id"]
        self.priority = int(self.flow_json["priority"])
        self.match_element = MatchElement(match_json=self.flow_json["match"], controller="odl", flow=self)

    def parse_ryu_flow(self):

        self.table_id = self.flow_json["table_id"]
        self.priority = int(self.flow_json["priority"])
        self.match_element = MatchElement(match_json=self.flow_json["match"], controller="ryu", flow=self)

    def add_port_graph_edges(self):

        if not "instructions" in self.flow_json:
            print "Assuming this means to drop."
        else:
            if self.sw.network_graph.controller == "odl":
                self.instruction_set = InstructionSet(self.sw, self, self.flow_json["instructions"]["instruction"])

            elif self.sw.network_graph.controller == "ryu":
                self.instruction_set = InstructionSet(self.sw, self, self.flow_json["instructions"])

            self.applied_field_modifications = \
                self.instruction_set.applied_action_set.get_modified_fields_dict(self.match_element)
            port_graph_edge_status = self.instruction_set.applied_action_set.get_port_graph_edge_status()

            for out_port, output_action in port_graph_edge_status:

                outgoing_port = self.port_graph.get_port(
                    self.port_graph.get_outgoing_port_id(self.sw.node_id, out_port))

                e = self.port_graph.add_edge(self.sw.flow_tables[self.table_id].port,
                                               outgoing_port,
                                               (self, output_action),
                                               self.applied_match)

                self.port_graph_edges.append(e)

            self.written_field_modifications = \
                self.instruction_set.written_action_set.get_modified_fields_dict(self.match_element)
            port_graph_edge_status = self.instruction_set.written_action_set.get_port_graph_edge_status()

            for out_port, output_action in port_graph_edge_status:

                outgoing_port = self.port_graph.get_port(
                    self.port_graph.get_outgoing_port_id(self.sw.node_id, out_port))

                e = self.port_graph.add_edge(self.sw.flow_tables[self.table_id].port,
                                               outgoing_port,
                                               (self, output_action),
                                               self.applied_match)

                self.port_graph_edges.append(e)




            # See the edge impact of any go-to-table instruction
            if self.instruction_set.goto_table:

                e = self.port_graph.add_edge(self.sw.flow_tables[self.table_id].port,
                                               self.sw.flow_tables[self.instruction_set.goto_table].port,
                                               (self, None),
                                               self.applied_match)

                self.port_graph_edges.append(e)

    def update_port_graph_edges(self):

        for src_port_id, dst_port_id, key in self.port_graph_edges:
            action = key[1]

            # TODO: If there is no action here (why isn't there one)
            if action:
                if self.sw.port_graph.get_port(dst_port_id).state != "down":
                    action.update_active_status()
                else:
                    action.is_active = False

class FlowTable():
    def __init__(self, sw, table_id, flow_list):

        self.sw = sw
        self.network_graph = sw.network_graph
        self.table_id = table_id
        self.flows = []
        self.input_port = None
        self.port_graph = None

        for f in flow_list:
            f = Flow(sw, f)
            self.flows.append(f)

        #  Sort the flows list by priority
        self.flows = sorted(self.flows, key=lambda flow: flow.priority, reverse=True)

    def init_flow_table_port_graph(self):

        remaining_match = Traffic(init_wildcard=True)

        for flow in self.flows:
            intersection = flow.match.intersect(remaining_match)
            flow.port_graph = self.port_graph

            # Don't care about matches that have full empty fields
            if not intersection.is_empty():

                # See what is left after this rule is through
                remaining_match = flow.complement_traffic.intersect(remaining_match)
                flow.applied_match = intersection

                # Add the edges in the portgraph
                flow.add_port_graph_edges()
            else:
                # Say that this flow does not matter
                flow.applied_match = None

    def de_init_flow_table_port_graph(self):
        pass