__author__ = 'Rakesh Kumar'


import pprint

from netaddr import IPNetwork
from netaddr import IPAddress
from group_table import Action
from match import Match

class Flow():
    def __init__(self, sw, flow):

        self.sw = sw
        self.priority = int(flow["priority"])
        self.match = Match(flow["match"])
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

    def does_it_match(self, flow_match):

        # If the intersection exists.
        if self.match.intersect(flow_match):
            return True
        else:
            return False


    def does_it_forward(self, in_port, out_port):
        ret_val = False

        # Requiring that any single action has to forward it
        for action in self.written_actions:
            if action.does_it_forward(in_port, out_port):
                ret_val = True
                break

        return ret_val

    def passes_flow(self, flow_match, out_port):
        ret_val = False
        if self.does_it_match(flow_match):
            if self.does_it_forward(flow_match.in_port, out_port):
                ret_val = True

        return ret_val

class FlowTable():
    def __init__(self, sw, table_id, flow_list):

        self.sw = sw
        self.table_id = table_id
        self.flows = []

        for f in flow_list:
            f = Flow(sw, f)
            self.flows.append(f)

        #  Sort the flows list by priority
        self.flows = sorted(self.flows, key=lambda flow: flow.priority, reverse=True)

    def passes_flow(self, flow_match, out_port):
        ret_val = False
        for flow in self.flows:
            ret_val = flow.passes_flow(flow_match, out_port)

            # As soon as an admitting rule is found, stop looking further
            if ret_val:
                break

        return ret_val

    def get_highest_priority_matching_flow(self, table_matches_on):

        hpm_flow = None
        intersection = None

        for flow in self.flows:
            intersection = flow.match.intersect(table_matches_on)
            if intersection:
                hpm_flow = flow
                break

        return hpm_flow, intersection