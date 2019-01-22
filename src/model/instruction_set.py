__author__ = 'Rakesh Kumar'

from intervaltree_modified import Interval
from traffic import Traffic
from action_set import ActionSet
from action_set import Action


class Instruction:

    def __init__(self, sw, instruction_raw):

        self.instruction_raw = instruction_raw
        self.instruction_type = None
        self.sw = sw
        self.actions_list = []
        self.go_to_table = None

        if self.sw.network_graph.controller == "onos":
            self.parse_onos_instruction()

        elif self.sw.network_graph.controller == "ryu":
            self.parse_ryu_instruction()

        elif self.sw.network_graph.controller == "grpc":
            self.parse_grpc_instruction()

        else:
            raise NotImplementedError

    def parse_onos_instruction(self):

        if "deferred" in self.instruction_raw:
            if self.instruction_raw["deferred"]:
                raise NotImplementedError

                self.instruction_type = "write-actions"
                write_actions_json = self.instruction_raw["deferred"]
                for action_json in write_actions_json:
                    self.actions_list.append(Action(self.sw, action_json))

        elif "immediate" in self.instruction_raw:
            if self.instruction_raw["immediate"]:
                raise NotImplementedError
                self.instruction_type = "apply-actions"
                apply_actions_json = self.instruction_raw["immediate"]
                for action_json in apply_actions_json:
                    self.actions_list.append(Action(self.sw, action_json))

        elif "instructions" in self.instruction_raw:
            if self.instruction_raw["instructions"]:
                self.instruction_type = "apply-actions"
                apply_actions_json = self.instruction_raw["instructions"]
                for action_json in apply_actions_json:
                    self.actions_list.append(Action(self.sw, action_json))

        elif "tableTransition" in self.instruction_raw:
            self.instruction_type = "go-to-table"
            self.go_to_table = self.instruction_raw["go-to-table"]["table_id"]

    def parse_ryu_instruction(self):

        if self.instruction_raw["type"] == "WRITE_ACTIONS":
            self.instruction_type = "write-actions"
            for action_json in self.instruction_raw["actions"]:
                self.actions_list.append(Action(self.sw, action_json))

        elif self.instruction_raw["type"] == "APPLY_ACTIONS":
            self.instruction_type = "apply-actions"
            for action_json in self.instruction_raw["actions"]:
                self.actions_list.append(Action(self.sw, action_json))

        elif self.instruction_raw["type"] == "GOTO_TABLE":
            self.instruction_type = "go-to-table"
            self.go_to_table = self.instruction_raw["table_id"]

        #TODO: Other instructions...

    def parse_grpc_instruction(self):

        if self.instruction_raw.type == "WRITE_ACTIONS":
            self.instruction_type = "write-actions"
            for action_json in self.instruction_raw.actions:
                self.actions_list.append(Action(self.sw, action_json))

        elif self.instruction_raw.type == "APPLY_ACTIONS":
            self.instruction_type = "apply-actions"
            for action_json in self.instruction_raw.actions:
                self.actions_list.append(Action(self.sw, action_json))

        elif self.instruction_raw.type == "GOTO_TABLE":
            self.instruction_type = "go-to-table"
            self.go_to_table = self.instruction_raw.go_to_table_num

        #TODO: Other instructions...

class InstructionSet:

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

    def __init__(self, sw, flow, instructions_raw):

        self.instructions_raw = instructions_raw
        self.sw = sw
        self.flow = flow
        self.network_graph = self.sw.network_graph
        self.instruction_list = []
        self.goto_table = None

        if self.sw.network_graph.controller == "onos":
            self.parse_onos_instruction_set()
        elif self.sw.network_graph.controller == "ryu":
            self.parse_ryu_instruction_set()
        elif self.sw.network_graph.controller == "grpc":
            self.parse_grpc_instruction_set()
        else:
            raise NotImplementedError

        self.applied_action_set = ActionSet(self.sw)
        self.written_action_set = ActionSet(self.sw)

    def parse_onos_instruction_set(self):

        for instruction_type_key in self.instructions_raw:

            instruction_raw = {instruction_type_key: self.instructions_raw[instruction_type_key]}

            instruction = Instruction(self.sw, instruction_raw)
            self.instruction_list.append(instruction)

    def parse_ryu_instruction_set(self):

        for instruction_raw in self.instructions_raw:
            instruction = Instruction(self.sw, instruction_raw)
            self.instruction_list.append(instruction)
            
    def parse_grpc_instruction_set(self):

        for instruction_raw in self.instructions_raw:
            instruction = Instruction(self.sw, instruction_raw)
            self.instruction_list.append(instruction)

    def populate_action_sets_for_port_graph_edges(self):

        for instruction in self.instruction_list:
            if instruction.instruction_type == "apply-actions":
                self.applied_action_set.remove_all_actions()
                self.applied_action_set.add_all_actions(instruction.actions_list)
            elif instruction.instruction_type == "write-actions":
                self.written_action_set.remove_all_actions()
                self.written_action_set.add_all_actions(instruction.actions_list)
            elif instruction.instruction_type == "go-to-table":
                self.goto_table = instruction.go_to_table

            # TODO: Handle clear-actions case
            # TODO: Handle meter instruction
            # TODO: Write meta-data case

    def get_applied_port_graph_edges(self):

        applied_port_graph_edges = []

        output_actions = self.applied_action_set.get_action_set_output_action_edges(self.flow.match.match_field_values["in_port"])

        for out_port, output_action in output_actions:

            applied_modifications = self.applied_action_set.get_modified_fields_dict(self.flow.traffic_element)
            written_modifications = self.written_action_set.get_modified_fields_dict(self.flow.traffic_element)

            if output_action.bucket != None:
                bucket_modifications = output_action.bucket.action_set.get_modified_fields_dict(self.flow.traffic_element)
                applied_modifications.update(bucket_modifications)

            output_action.instruction_type = "applied"
            egress_node = self.sw.port_graph.get_egress_node(self.sw.node_id, out_port)

            # TODO: Perhaps due to quirks of software implementation self.flow.applied_traffic should not include
            # the out_port as in_port. Basically if you are going to bolt out of the same port where you came in
            # You HAVE to use IN_PORT as outport...

            if "vlan_id" in applied_modifications or "vlan_id" in written_modifications:
                new_applied_traffic = Traffic(init_wildcard=False)
                filtered_te_list = []
                for te in self.flow.applied_traffic.traffic_elements:
                    if te.is_traffic_field_wildcard(te.traffic_fields["has_vlan_tag"]):
                        filtered_te_list.append(te)
                    else:
                        if Interval(1, 2) in te.traffic_fields["has_vlan_tag"]:
                            filtered_te_list.append(te)

                new_applied_traffic.add_traffic_elements(filtered_te_list)
                self.flow.applied_traffic = new_applied_traffic

            applied_port_graph_edges.append((egress_node,
                                             (self.flow.applied_traffic,
                                              output_action,
                                              applied_modifications,
                                              written_modifications)))

        return applied_port_graph_edges

    def get_written_port_graph_edges(self):

        written_port_graph_edges = []

        output_actions = self.written_action_set.get_action_set_output_action_edges(self.flow.match.match_field_values["in_port"])

        for out_port, output_action in output_actions:

            applied_modifications = self.applied_action_set.get_modified_fields_dict(self.flow.traffic_element)
            written_modifications = self.written_action_set.get_modified_fields_dict(self.flow.traffic_element)

            if output_action.bucket != None:
                bucket_modifications = output_action.bucket.action_set.get_modified_fields_dict(self.flow.traffic_element)
                written_modifications.update(bucket_modifications)

            output_action.instruction_type = "written"
            egress_node = self.sw.port_graph.get_egress_node(self.sw.node_id, out_port)

            # TODO: Perhaps due to quirks of software implementation self.flow.applied_traffic should not include
            # the out_port as in_port. Basically if you are going to bolt out of the same port where you came in
            # You HAVE to use IN_PORT as outport...

            if "vlan_id" in applied_modifications or "vlan_id" in written_modifications:
                new_applied_traffic = Traffic(init_wildcard=False)
                filtered_te_list = []
                for te in self.flow.applied_traffic.traffic_elements:
                    if te.is_traffic_field_wildcard(te.traffic_fields["has_vlan_tag"]):
                        filtered_te_list.append(te)
                    else:
                        if Interval(1, 2) in te.traffic_fields["has_vlan_tag"]:
                            filtered_te_list.append(te)

                new_applied_traffic.add_traffic_elements(filtered_te_list)
                self.flow.applied_traffic = new_applied_traffic

            written_port_graph_edges.append((egress_node,
                                             (self.flow.applied_traffic,
                                              output_action,
                                              applied_modifications,
                                              written_modifications)))

        return written_port_graph_edges