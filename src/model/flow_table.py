__author__ = 'Rakesh Kumar'


from action_set import Action, ActionSet
from match_element import MatchElement
from traffic import Traffic
from instruction_set import InstructionSet

class Flow():

    def __hash__(self):
        return hash(str(self.sw.node_id) + str(self.table_id) + str(self.id))

    def __init__(self, sw, flow_json):

        self.sw = sw
        self.network_graph = sw.network_graph
        self.flow_json = flow_json
        self.table_id = flow_json["table_id"]
        self.id = flow_json["id"]
        self.priority = int(flow_json["priority"])
        self.match_element = MatchElement(flow_json["match"], self)

        self.written_actions = []
        self.applied_actions = []
        self.go_to_table = None

        # Port Graph Stuff
        self.port_graph = None
        self.match = Traffic()
        self.match.match_elements.append(self.match_element)

        complement_match_elements = self.match_element.get_complement_match_elements()
        self.complement_traffic = Traffic()
        self.complement_traffic.add_match_elements(complement_match_elements)

        self.applied_match = None
        self.port_graph_edges = []

        if "instructions" in flow_json:

            # Go through instructions
            for instruction_json in flow_json["instructions"]["instruction"]:

                if "write-actions" in instruction_json:
                    write_actions_json = instruction_json["write-actions"]
                    for action_json in write_actions_json["action"]:
                        self.written_actions.append(Action(sw, action_json))

                if "apply-actions" in instruction_json:
                    apply_actions_json = instruction_json["apply-actions"]
                    for action_json in apply_actions_json["action"]:
                        self.applied_actions.append(Action(sw, action_json))

                if "go-to-table" in instruction_json:
                    self.go_to_table = instruction_json["go-to-table"]["table_id"]

                # TODO: Handle meter instruction
                # TODO: Handle clear-actions case
                # TODO: Write meta-data case
                # TODO: Handle apply-actions case (SEL however, does not support this yet)
        else:
            # Interpreting Lack of instructions as Drop
            self.drop = True

    # Prepares a dictionary keyed by field_name with the value from the match element of flow to indicate
    # what it is supposed to have been before it got modified (not what it is set to)

    def prepare_field_modifications(self, modified_fields_list):
        field_modifications = {}

        for field in modified_fields_list:
            field_modifications[field] = self.match_element.match_fields[field]

        return field_modifications

    def add_port_graph_edges(self):

        if not "instructions" in self.flow_json:
            print "Assuming this means to drop."
        else:
            self.instructions = InstructionSet(self.sw, self, self.flow_json["instructions"]["instruction"])

            applied_modified_fields_list = self.instructions.applied_action_set.get_modified_fields_list()
            self.applied_field_modifications = self.prepare_field_modifications(applied_modified_fields_list)
            port_graph_edge_status = self.instructions.applied_action_set.get_port_graph_edge_status()

            for out_port, output_action in port_graph_edge_status:

                outgoing_port = self.port_graph.get_port(
                    self.port_graph.get_outgoing_port_id(self.sw.node_id, out_port))

                e = self.port_graph.add_edge(self.sw.flow_tables[self.table_id].port,
                                               outgoing_port,
                                               (self, output_action),
                                               self.applied_match)

                self.port_graph_edges.append(e)


            written_modified_fields_list = self.instructions.written_action_set.get_modified_fields_list()
            self.written_field_modifications = self.prepare_field_modifications(written_modified_fields_list)
            port_graph_edge_status = self.instructions.written_action_set.get_port_graph_edge_status()

            for out_port, output_action in port_graph_edge_status:

                outgoing_port = self.port_graph.get_port(
                    self.port_graph.get_outgoing_port_id(self.sw.node_id, out_port))

                e = self.port_graph.add_edge(self.sw.flow_tables[self.table_id].port,
                                               outgoing_port,
                                               (self, output_action),
                                               self.applied_match)

                self.port_graph_edges.append(e)




            # See the edge impact of any go-to-table instruction
            if self.instructions.goto_table:

                e = self.port_graph.add_edge(self.sw.flow_tables[self.table_id].port,
                                               self.sw.flow_tables[self.instructions.goto_table].port,
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

    def get_highest_priority_matching_flow(self, table_matches_on):

        hpm_flow = None
        intersection = None

        for flow in self.flows:
            intersection = flow.match_element.intersect(table_matches_on)
            if intersection:
                hpm_flow = flow
                break

        return hpm_flow, intersection

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