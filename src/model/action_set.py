__author__ = 'Rakesh Kumar'

from match import OdlMatchJsonParser
from match import ryu_field_names_mapping
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

    def __init__(self, sw, action_json):

        self.action_json = action_json
        self.sw = sw
        self.action_type = None
        self.bucket = None
        self.instruction_type = None

        self.vuln_rank = 0

        # Captures what the action is doing.
        self.modified_field = None
        self.field_modified_to = None

        if self.sw.network_graph.controller == "odl":
            self.parse_odl_action_json()

        elif self.sw.network_graph.controller == "ryu":
            self.parse_ryu_action_json()

        elif self.sw.network_graph.controller == "sel":
            self.parse_sel_action_json()


    def parse_odl_action_json(self):

        self.order = self.action_json["order"]

        if "output-action" in self.action_json:
            self.action_type = "output"

            if self.action_json["output-action"]["output-node-connector"] == u"CONTROLLER":
                self.out_port = self.sw.network_graph.OFPP_CONTROLLER
            elif self.action_json["output-action"]["output-node-connector"] == u"INPORT":
                self.out_port = self.sw.network_graph.OFPP_IN
            else:
                self.out_port = int(self.action_json["output-action"]["output-node-connector"])

        if "group-action" in self.action_json:
            self.action_type = "group"
            self.group_id = int(self.action_json["group-action"]["group-id"])

        if "push-vlan-action" in self.action_json:
            self.action_type = "push_vlan"
            self.vlan_ethernet_type = self.action_json["push-vlan-action"]["ethernet-type"]

        if "pop-vlan-action" in self.action_json:
            self.action_type = "pop_vlan"

        if "set-field" in self.action_json:
            self.action_type = "set_field"
            self.set_field_match_json = self.action_json["set-field"]
            mjp = OdlMatchJsonParser(self.action_json["set-field"])
            if mjp.keys():
                self.modified_field = mjp.keys()[0]
                self.field_modified_to = mjp[self.modified_field]


    def parse_sel_action_json(self):
        self.order = self.action_json["setOrder"]

        if self.action_json["actionType"] == 'Output':
            self.action_type = "output"
            if int(self.action_json["outPort"]) == 4294967293:
                self.out_port = self.sw.network_graph.OFPP_CONTROLLER
            else:
                self.out_port = int(self.action_json["outPort"])

        if self.action_json["actionType"] == 'Group':
            self.action_type = "group"
            self.group_id = int(self.action_json["groupId"])

        # if self.action_json["actionType"] == 'PushVlan':
        #     self.action_type = "push_vlan"
        #     self.vlan_ethernet_type = self.action_json['ethernetType']
        #
        # if self.action_json["actionType"] == 'PopVlan':
        #     self.action_type = "pop_vlan"

        if self.action_json["actionType"] == 'SetField':
            self.action_type = "set_field"
            if self.action_json["field"]["@odata.type"] == "#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.MatchFields.VlanVid":
                self.modified_field = "vlan_id"
                self.field_modified_to = int(self.action_json["field"]["value"])
            else:
                raise NotImplementedError



    def parse_ryu_action_json(self):

        if self.action_json.startswith("OUTPUT"):
            self.action_type = "output"
            output_port = self.action_json.split(":")[1]
            self.out_port = int(output_port)

        if self.action_json.startswith("SET_FIELD"):
            self.action_type = "set_field"
            field_mod = self.action_json[self.action_json.find("{") + 1:]
            self.modified_field = ryu_field_names_mapping[field_mod[0:field_mod.find(":")]]
            self.field_modified_to = field_mod[field_mod.find(":") + 1:field_mod.find("}")]

            if self.modified_field == "vlan_id":
                self.field_modified_to = int(self.field_modified_to) - 0x1000

        if self.action_json.startswith("GROUP"):
            self.action_type = "group"
            self.group_id = int(self.action_json[self.action_json.find(":") + 1:])

        # if "push-vlan-action" in self.action_json:
        #     self.action_type = "push_vlan"
        #     self.vlan_ethernet_type = self.action_json["push-vlan-action"]["ethernet-type"]
        #
        # if "pop-vlan-action" in self.action_json:
        #     self.action_type = "pop_vlan"

    def is_failover_action(self):
        return (self.bucket and self.bucket.group.group_type == self.sw.network_graph.GROUP_FF)

    def perform_edge_failover(self):

        muted_ports = []
        unmuted_port = None

        for bucket_rank in range(len(self.bucket.group.bucket_list)):
            
            this_bucket = self.bucket.group.bucket_list[bucket_rank]

            if this_bucket.is_live():

                if not unmuted_port:
                    unmuted_port = (this_bucket.watch_port, bucket_rank)
                else:
                    muted_ports.append((this_bucket.watch_port, bucket_rank))
            else:
                muted_ports.append((this_bucket.watch_port, bucket_rank))

        return muted_ports, unmuted_port

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

        # network_graphling the ActionSet as a dictionary of lists, keyed by various actions.
        # These actions may be tucked away inside a group too and the type might be group

        self.action_dict = defaultdict(list)
        self.sw = sw

    def add_all_actions(self, action_list, intersection):

        for action in action_list:

            if action.action_type == "group":
                if action.group_id in self.sw.group_table.groups:
                    group_all_action_list =  self.sw.group_table.groups[action.group_id].get_action_list()
                    self.add_all_actions(group_all_action_list, intersection)
                else:
                    raise Exception("Odd that a group_id is not provided in a group action")
            else:
                self.action_dict[action.action_type].append(action)

    def get_modified_fields_dict(self, flow_match_element):
        modified_fields_dict = {}

        # Capture the value before (in principle and after) the modification in a tuple
        for set_action in self.action_dict["set_field"]:
            modified_fields_dict[set_action.modified_field] = (flow_match_element, set_action.field_modified_to)

        return modified_fields_dict

    def get_action_set_port_graph_edges(self):

        port_graph_edges = []

        for output_action in self.action_dict["output"]:

            if int(output_action.out_port) == self.sw.network_graph.OFPP_CONTROLLER:
                continue

            if int(output_action.out_port) == self.sw.network_graph.OFPP_NORMAL:
                continue

            if output_action.is_failover_action():

                # If the output port is specified to be same as input port
                if int(self.sw.network_graph.OFPP_IN) == int(output_action.out_port):

                    # Consider all possible ports
                    for in_port in self.sw.ports:

                        # if they are currently up
                        if self.sw.ports[in_port].state != "up":
                            continue

                        # If they are not the watch port of actions that may have come before
                        # this action in a failover rule, because that port has failed already, no need to
                        # add an edge going there
                        if in_port in output_action.bucket.prior_failed_ports():
                            continue

                        port_graph_edges.append((str(in_port), output_action))

                else:
                    # Add an edge, only if the output_port is currently up
                    if self.sw.ports[output_action.out_port].state == "up":
                        port_graph_edges.append((str(output_action.out_port), output_action))

            else:
                # If the output port is specified to be same as input port
                if int(self.sw.network_graph.OFPP_IN) == int(output_action.out_port):

                    # Consider all possible ports
                    for in_port in self.sw.ports:
                        # if they are currently up
                        if self.sw.ports[in_port].state != "up":
                            continue
                        port_graph_edges.append((str(in_port), output_action))

                else:

                    # Add an edge, only if the output_port is currently up
                    if self.sw.ports[output_action.out_port].state == "up":
                        port_graph_edges.append((str(output_action.out_port), output_action))


        return port_graph_edges
