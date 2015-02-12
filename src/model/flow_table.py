__author__ = 'Rakesh Kumar'


import pprint

from netaddr import IPNetwork
from netaddr import IPAddress

from action import Action, ActionSet
from match import MatchElement
from match import Match

class Flow():

    def __hash__(self):
        return hash(str(self.sw.node_id) + str(self.table_id) + str(self.id))

    def __init__(self, sw, flow):

        self.sw = sw
        self.model = sw.model
        self.table_id = flow["table_id"]
        self.id = flow["id"]
        self.priority = int(flow["priority"])
        self.match_element = MatchElement(flow["match"], self)
        self.complement_match = self.match_element.complement_match(self)

        self.applied_match = None

        self.written_actions = []
        self.applied_actions = []
        self.go_to_table = None

        # Go through instructions
        for instruction_json in flow["instructions"]["instruction"]:

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


class FlowTable():
    def __init__(self, sw, table_id, flow_list):

        self.sw = sw
        self.model = sw.model
        self.table_id = table_id
        self.flows = []
        self.input_port = None

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
            if not intersection.has_empty_field():
                hpm_flow = flow
                break

        return hpm_flow, intersection

    def get_next_matching_flow(self, table_matches_on):

        intersection = None
        remaining_match = None

        for flow in self.flows:
            intersection = flow.match.intersect(table_matches_on)
            if intersection:
                remaining_match = flow.match.complement(table_matches_on)
                yield flow, intersection, remaining_match

    def compute_applied_matches(self, in_match):

        remaining_match = in_match

        for flow in self.flows:

            intersection = flow.match_element.intersect(remaining_match)

            # Don't care about matches that have full empty fields
            if not intersection.has_empty_field():

                # See what is left after this rule is through
                remaining_match = flow.complement_match.intersect(remaining_match)
                flow.applied_match = intersection
            else:
                
                # Say that this flow does not matter
                flow.applied_match = None

    def add_port_graph_edges(self):

        for flow in self.flows:

            #Actions will be gathered here...
            written_action_set = ActionSet(self.sw)

            #TODO. Figure out this.
            if flow.applied_actions:
                table_applied_action_set = ActionSet(self)
                table_applied_action_set.add_actions(flow.applied_actions, flow.applied_match)
                written_action_set.add_actions(flow.applied_actions, flow.applied_match)
            else:
                pass
                #next_table_matches_on = in_port_match

            # If there are any written-actions that hpm_flow does, accumulate them
            if flow.written_actions:
                written_action_set.add_actions(flow.written_actions, flow.applied_match)

            # flow has an instruction to go to another table, add a port in port graph for that...
            if flow.go_to_table:
                self.model.port_graph.add_edge(self.sw.flow_tables[flow.table_id].input_port,
                                               self.sw.flow_tables[flow.go_to_table].input_port,
                                               flow.applied_match,
                                               written_action_set)