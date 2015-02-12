__author__ = 'Rakesh Kumar'

from action import ActionSet
from action import Action

class Instructions():

    def __init__(self, sw, instructions_json):

        self.sw = sw
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


    def get_actions_to_write(self):
        #Actions will be gathered here.
        # ..
        written_action_set = ActionSet(self.sw)

        #TODO. Figure out this.
        if self.applied_actions:
            table_applied_action_set = ActionSet(self)
            table_applied_action_set.add_actions(self.applied_actions, self.applied_match)
            written_action_set.add_actions(self.applied_actions, self.applied_match)
        else:
            pass
            #next_table_matches_on = in_port_match

        # If there are any written-actions that hpm_flow does, accumulate them
        if self.written_actions:
            written_action_set.add_actions(self.written_actions, self.applied_match)

        # flow has an instruction to go to another table, add a port in port graph for that...
        if self.go_to_table:
            self.model.port_graph.add_edge(self.sw.flow_tables[self.table_id].input_port,
                                           self.sw.flow_tables[self.go_to_table].input_port,
                                           self.applied_match,
                                           written_action_set)