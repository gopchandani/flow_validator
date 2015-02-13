__author__ = 'Rakesh Kumar'

from action_set import ActionSet
from action_set import Action

class Instruction():

    def __init__(self, sw, instruction_json):
        self.instruction_type = None
        self.sw = sw

        if "write-actions" in instruction_json:
            self.instruction_type = "write-actions"
            write_actions_json = instruction_json["write-actions"]
            for action_json in write_actions_json["action"]:
                self.written_actions.append(Action(sw, action_json))

        elif "apply-actions" in instruction_json:
            self.instruction_type = "apply-actions"
            apply_actions_json = instruction_json["apply-actions"]
            for action_json in apply_actions_json["action"]:
                self.applied_actions.append(Action(sw, action_json))

        elif "go-to-table" in instruction_json:
            self.instruction_type = "go-to-table"
            self.go_to_table = instruction_json["go-to-table"]["table_id"]

        # TODO: Handle meter instruction
        # TODO: Handle clear-actions case
        # TODO: Write meta-data case
        # TODO: Handle apply-actions case (SEL however, does not support this yet)

class InstructionSet():

    '''
    As per OF1.3 specification:

    Optional Instruction:   Meter meter id: Direct packet to the specified meter. As the result of the metering,
                            the packet may be dropped.
    Optional Instruction:   Apply-Actions action(s): Applies the specific action(s) immediately, without any change to
                            the Action Set. This instruction may be used to modify the packet between two tables or to
                            execute multiple actions of the same type.
    Optional Instruction:   Clear-Actions: Clears all the actions in the action set immediately.
    Required Instruction:   Write-Actions action(s): Merges the specified action(s) into the current action set.
                            If an action of the given type exists in the current set, overwrite it, otherwise add it.
    Optional Instruction:   Write-Metadata metadata / mask: Writes the masked metadata value into the metadata field.
                            The mask specifies which bits of the metadata register should be modified
                            (i.e. new metadata = old metadata & mask | value & mask).
    Required Instruction:   Goto-Table next-table-id: Indicates the next table in the processing pipeline.
                            The table-id must be greater than the current table-id.
                            The flow entries of last table of the pipeline can not include this instruction

    The instruction set associated with a flow entry contains a maximum of one instruction of each type.
    The instructions of the set execute in the order specified by this above list.
    In practice, the only constraints are that the Meter instruction is executed before the Apply-Actions instruction,
    the Clear-Actions instruction is executed before the Write-Actions instruction,
    and that Goto-Table is executed last.
    '''

    def __init__(self, sw, flow, instructions_json):

        self.sw = sw
        self.flow = flow
        self.model = self.sw.model

        self.instruction_list = []
        self.written_actions = []
        self.applied_actions = []
        self.go_to_table = None

        for instruction_json in instructions_json:
            self.instruction_list.append(Instruction(sw, instructions_json))

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