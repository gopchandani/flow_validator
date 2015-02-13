__author__ = 'Rakesh Kumar'

from action import ActionSet
from action import Action

class Instructions():

    def __init__(self, sw, flow, instructions_json):

        self.sw = sw
        self.flow = flow
        self.model = self.sw.model
        self.written_actions = []
        self.applied_actions = []
        self.go_to_table = None

        # Go through instructions
        for instruction_json in instructions_json:

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


    def add_port_graph_edges(self):

        match_action_tuple_list = []

        match_for_port = self.flow.applied_match
        actions_for_port = ActionSet(self.sw)

        # Instructions dictate that things be done immediately and may include output
        if self.applied_actions:
            pass

        # These things are applied upon traversal of the edge
        if self.written_actions:
            pass


        if self.go_to_table:
            match_action_tuple_list.append((self.sw.flow_tables[self.flow.table_id].port,
                                            self.sw.flow_tables[self.go_to_table].port,
                                            match_for_port,
                                            actions_for_port))



        # Add them all in
        for src, dst, match, actions in match_action_tuple_list:
            self.model.port_graph.add_edge(src, dst, match, actions)

        return match_action_tuple_list