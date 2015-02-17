__author__ = 'Rakesh Kumar'

from action_set import ActionSet
from action_set import Action

class Instruction():

    def __init__(self, sw, instruction_json):
        self.instruction_type = None
        self.sw = sw
        self.actions_list = []
        self.go_to_table = None

        if "write-actions" in instruction_json:
            self.instruction_type = "write-actions"
            write_actions_json = instruction_json["write-actions"]
            for action_json in write_actions_json["action"]:
                self.actions_list.append(Action(sw, action_json))

        elif "apply-actions" in instruction_json:
            self.instruction_type = "apply-actions"
            apply_actions_json = instruction_json["apply-actions"]
            for action_json in apply_actions_json["action"]:
                self.actions_list.append(Action(sw, action_json))

        elif "go-to-table" in instruction_json:
            self.instruction_type = "go-to-table"
            self.go_to_table = instruction_json["go-to-table"]["table_id"]

class InstructionSet():

    '''
    As per OF1.3 specification:

    Optional Instruction:   Meter meter id: Direct packet to the specified meter. As the result of the metering,
                            the packet may be dropped.

    Optional Instruction:   Apply-Actions action(s): Applies the specific action(s) immediately, without any change to
                            the Action Set. This instruction may be used to modify the packet between two tables or to
                            execute multiple actions of the same type.
                            If the action list contains an output action, a copy of the packet is forwarded in its
                            current state to the desired port. If the list contains group actions, a copy of the
                            packet in its current state is processed by the relevant group buckets.
                            After the execution of the action list in an Apply-Actions instruction, pipeline execution
                            continues on the modified packet. The action set of the packet is unchanged by
                            the execution of the action list.

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

        for instruction_json in instructions_json:
            instruction = Instruction(sw, instruction_json)

            #Apply-Action has to be the first one, so reorganizing that...
            if instruction.instruction_type == "":
                self.instruction_list.insert(0, instruction)
            else:
                self.instruction_list.append(instruction)

    def add_port_graph_edges(self):

        port_additions = []

        # match_for_port is what matched and it will be modified by any apply-action instructions below
        match_for_port = self.flow.applied_match

        for instruction in self.instruction_list:

            # Instructions dictate that things be done immediately and may include output
            if instruction.instruction_type == "apply-actions":

                # Put all the actions under this instruction in an ActionSet and mix it up...
                applied_action_set = ActionSet(self.sw)
                applied_action_set.add_all_actions(instruction.actions_list, match_for_port)

                # Get the resulting match and have it be applied
                match_for_port = applied_action_set.get_resulting_match_2(match_for_port)

                #Check to see if applied_action_set has any output edges to contribute
                out_port_and_active_status_tuple_list = \
                    applied_action_set.get_out_port_and_active_status_tuple(match_for_port)

                for out_port, active_status in out_port_and_active_status_tuple_list:
                    if out_port == "4294967293":
                        port_additions.append((self.sw.flow_tables[self.flow.table_id].port,
                                                        self.sw.model.port_graph.get_port(str(out_port)),
                                                        match_for_port,
                                                        None, active_status))
                    else:
                        port_additions.append((self.sw.flow_tables[self.flow.table_id].port,
                                                        self.sw.ports[out_port],
                                                        match_for_port,
                                                        None, active_status))

            # These things affect the next table, so the edge to next table is going to contain these two
            # types of "edits" on the ActionSet
            elif instruction.instruction_type == "write-actions":
                
                # Put all the actions under this instruction in an ActionSet and pass it down .
                written_action_set = ActionSet(self.sw)
                written_action_set.add_all_actions(instruction.actions_list, match_for_port)

                #Check to see if written_action_set has any output edges to contribute
                out_port_and_active_status_tuple_list = \
                    written_action_set.get_out_port_and_active_status_tuple(match_for_port)

                for out_port, active_status in out_port_and_active_status_tuple_list:
                    if out_port == 4294967293:
                        port_additions.append((self.sw.flow_tables[self.flow.table_id].port,
                                                        self.sw.model.port_graph.get_port(out_port),
                                                        match_for_port,
                                                        written_action_set, active_status))
                    else:
                        port_additions.append((self.sw.flow_tables[self.flow.table_id].port,
                                                        self.sw.ports[out_port],
                                                        match_for_port,
                                                        written_action_set, active_status))


            elif instruction.instruction_type == "go-to-table":
                port_additions.append((self.sw.flow_tables[self.flow.table_id].port,
                                                self.sw.flow_tables[instruction.go_to_table].port,
                                                match_for_port,
                                                None, True))
                
            # TODO: Handle meter instruction
            # TODO: Handle clear-actions case
            # TODO: Write meta-data case
            # TODO: Handle apply-actions case (SEL however, does not support this yet)

        # Add them all in
        for src, dst, match, actions, active_status in port_additions:
            self.model.port_graph.add_edge(src, dst, match, actions, active_status)
