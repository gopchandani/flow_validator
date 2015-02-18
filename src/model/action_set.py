__author__ = 'Rakesh Kumar'

from match import Match
from collections import defaultdict

class Action():
    '''
     As per OF1.3 specification:

    Required Action: Output. The Output action forwards a packet to a specified OpenFlow port.
                            OpenFlow switches must support forwarding to physical ports, switch-defined logical ports
                            and the required reserved ports.

    Optional Action: Set-Queue. The set-queue action sets the queue id for a packet. When the packet is forwarded to
                            a port using the output action, the queue id determines which queue attached to this port
                            is used for scheduling and forwarding the packet. Forwarding behavior is dictated by the
                            configuration of the queue and is used to provide basic Quality-of-Service (QoS) support

    Required Action: Drop. There is no explicit action to represent drops. Instead, packets whose action sets have no
                            output actions should be dropped. This result could come from empty instruction sets or
                            empty action buckets in the processing pipeline, or after executing a Clear-Actions
                            instruction.

    Required Action: Group. Process the packet through the specified group. The exact interpretation depends on group
                            type.
    Optional Action: Push-Tag/Pop-Tag. Switches may support the ability to push/pop tags. To aid
                            integration with existing networks, we suggest that the ability to push/pop VLAN tags be
                            supported.
    '''

    def __init__(self, sw, action_json, is_active=True):

        self.sw = sw
        self.matched_flow = None
        self.order = action_json["order"]
        self.action_type = None
        self.is_active = is_active

        if "output-action" in action_json:
            self.action_type = "output"

            if action_json["output-action"]["output-node-connector"] == "CONTROLLER":
                self.out_port = self.sw.model.OFPP_CONTROLLER
            else:
                self.out_port = action_json["output-action"]["output-node-connector"]

        if "group-action" in action_json:
            self.action_type = "group"
            self.group_id = action_json["group-action"]["group-id"]

        if "push-vlan-action" in action_json:
            self.action_type = "push_vlan"
            self.vlan_ethernet_type = action_json["push-vlan-action"]["ethernet-type"]

        if "pop-vlan-action" in action_json:
            self.action_type = "pop_vlan"

        if "set-field" in action_json:
            self.action_type = "set_field"
            self.set_field_match_json = action_json["set-field"]

class ActionSet():

    '''
    As per OF1.3 specification:

    An action set is associated with each packet.
    An action set contains a maximum of one action of each type.
    The set-field actions are identified by their field types, therefore the action set contains a maximum of one
    set-field action for each field type (i.e. multiple fields can be set). When multiple actions of the same type are
    required, e.g. pushing multiple MPLS labels or popping multiple MPLS labels, the Apply-Actions instruction may be
    used.


    The actions in an action set are applied in the order specified below,
    regardless of the order that they were added to the set.
    If an action set contains a group action, the actions in the appropriate action bucket
    of the group are also applied in the order specified below. The switch may support arbitrary
    action execution order through the action list of the Apply-Actions instruction.

    1. copy TTL inwards: apply copy TTL inward actions to the packet
    2. pop: apply all tag pop actions to the packet
    3. push-MPLS: apply MPLS tag push action to the packet
    4. push-PBB: apply PBB tag push action to the packet
    5. push-VLAN: apply VLAN tag push action to the packet
    6. copy TTL outwards: apply copy TTL outwards action to the packet
    7. decrement TTL: apply decrement TTL action to the packet
    8. set: apply all set-field actions to the packet
    9. qos: apply all QoS actions, such as set queue to the packet
    10. group: if a group action is specified, apply the actions of the relevant group bucket(s) in the order specified by this list
    11. output: if no group action is specified, forward the packet on the port specified by the output action

    The output action in the action set is executed last. If both an output action and a group action are specified
    in an action set, the output action is ignored and the group action takes precedence.
    If no output action and no group action were specified in an action set, the packet is dropped.
    The execution of groups is recursive if the switch supports it; a group bucket may specify another group,
    in which case the execution of actions traverses all the groups specified by the group configuration.

    '''

    def __init__(self, sw):

        # Modelling the ActionSet as a dictionary of lists, keyed by various actions.
        # These actions may be tucked away inside a group too and the type might be group

        self.action_dict = defaultdict(list)
        self.sw = sw


    # These  essentially turn the nested action_list which may contain group actions in it,
    # into a simple dictionary keyed by type and values containing the action itself
    # This is a way to essentially sort actions from being in groups into being categorized by their type

    def add_active_actions(self, action_list, intersection):

        for action in action_list:

            if action.action_type == "group":
                if action.group_id in self.sw.group_table.groups:
                    group_active_action_list =  self.sw.group_table.groups[action.group_id].get_active_action_list()
                    self.add_active_actions(group_active_action_list, intersection)
                else:
                    raise Exception("Odd that a group_id is not provided in a group action")
            else:
                action.matched_flow = intersection
                self.action_dict[action.action_type].append(action)

    def add_all_actions(self, action_list, intersection):

        for action in action_list:

            if action.action_type == "group":
                if action.group_id in self.sw.group_table.groups:
                    group_all_action_list =  self.sw.group_table.groups[action.group_id].get_all_action_list()
                    self.add_all_actions(group_all_action_list, intersection)
                else:
                    raise Exception("Odd that a group_id is not provided in a group action")
            else:
                action.matched_flow = intersection
                self.action_dict[action.action_type].append(action)

    def get_resulting_match_element(self, input_match):

        output_match = input_match

        # Go through the operations that are performed to the match before the packet is sent out
        if "pop_vlan" in self.action_dict:
            output_match.set_match_field_element("has_vlan_tag", int(False))

        if "push_vlan" in self.action_dict:
            output_match.set_match_field_element("has_vlan_tag", int(True))

        if "set_field" in self.action_dict:
            output_match.set_fields_with_match_json(self.action_dict["set_field"][0].set_field_match_json)

        return output_match

    def get_resulting_match(self, input_match):

        output_match = input_match

        # Go through the operations that are performed to the match before the packet is sent out
        if "pop_vlan" in self.action_dict:
            output_match.set_field("has_vlan_tag", int(False))

        if "push_vlan" in self.action_dict:
            output_match.set_field("has_vlan_tag", int(True))

        if "set_field" in self.action_dict:
            output_match.set_field(match_json=self.action_dict["set_field"][0].set_field_match_json)

        return output_match


    def get_out_port_matches(self, in_port_match, in_port):

        out_port_match = {}

        #  For each output action, there is a corresponding out_port_match entry
        for output_action in self.action_dict["output"]:

            output_match = self.get_resulting_match_element(output_action.matched_flow)

            if self.sw.model.OFPP_IN == int(output_action.out_port):
                out_port_match[int(in_port)] = output_match
            else:
                out_port_match[int(output_action.out_port)] = output_match

        return out_port_match

    def get_out_port_and_active_status_tuple(self):

        out_port_list = []

        #  For each output action, there is a corresponding out_port_match entry
        for output_action in self.action_dict["output"]:

            if self.sw.model.OFPP_IN == int(output_action.out_port):

                # Consider all possible ports...
                for in_port in self.sw.ports:
                    out_port_list.append((str(in_port), output_action.is_active))
            else:
                out_port_list.append((str(output_action.out_port), output_action.is_active))

        return out_port_list