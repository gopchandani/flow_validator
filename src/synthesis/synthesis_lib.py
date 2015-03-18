__author__ = 'Rakesh Kumar'


import pprint
import time
import httplib2
import json

from model.network_graph import NetworkGraph


class SynthesisLib():

    def __init__(self, controller_host, controller_port, model=None, master_switch=False):

        if not model:
            self.model = NetworkGraph()
        else:
            self.model = model

        self.controller_host = controller_host
        self.controller_port = controller_port

        self.master_switch = master_switch

        self.group_id_cntr = 0
        self.flow_id_cntr = 0

        self.h = httplib2.Http(".cache")
        self.h.add_credentials('admin', 'admin')

        # Table 0 contains the reverse rules (they should be examined first)
        self.reverse_rules_table_id = 0

        # Table 1 contains any rules that have to do with vlan tag push/pop
        self.vlan_rules_table_id = 1

        # Table 2 contains any rules associated with forwarding host traffic
        self.mac_forwarding_table_id = 2

        # Table 3 contains the actual forwarding rules
        self.ip_forwarding_table_id = 3


    def _push_change(self, url, pushed_content):

        time.sleep(0.1)

        resp, content = self.h.request(url, "PUT",
                                       headers={'Content-Type': 'application/json; charset=UTF-8'},
                                       body=json.dumps(pushed_content))

        #resp = {"status": "200"}
        #pprint.pprint(pushed_content)

        if resp["status"] == "200":
            print "Pushed Successfully:", pushed_content.keys()[0]
            #print resp["status"]
        else:
            print "Problem Pushing:", pushed_content.keys()[0]
            print "resp:", resp, "content:", content
            pprint.pprint(pushed_content)


    def create_group_url(self, node_id,  group_id):
        return "http://" + self.controller_host + ":" + self.controller_port + \
               "/restconf/config/opendaylight-inventory:nodes/node/" + \
               str(node_id) + '/group/' + str(group_id)

    def create_flow_url(self, node_id, table_id, flow_id):
        return "http://" + self.controller_host + ":" + self.controller_port + \
               "/restconf/config/opendaylight-inventory:nodes/node/" + \
               str(node_id) + "/table/" + str(table_id) + '/flow/' + str(flow_id)

    def _push_flow(self, sw, flow):

        flow_id = flow["flow-node-inventory:flow"]["id"]
        table_id = flow["flow-node-inventory:flow"]["table_id"]
        url = self.create_flow_url(sw, table_id, flow_id)
        self._push_change(url, flow)

    def _push_group(self, sw, group):

        group_id = group["flow-node-inventory:group"]["group-id"]
        url = self.create_group_url(sw, group_id)
        self._push_change(url, group)

    def _create_base_flow(self, table_id, priority):

        flow = dict()

        flow["flags"] = ""
        flow["table_id"] = table_id
        self.flow_id_cntr +=  1
        flow["id"] = self.flow_id_cntr
        flow["priority"] = priority
        flow["idle-timeout"] = 0
        flow["hard-timeout"] = 0
        flow["cookie"] = self.flow_id_cntr
        flow["cookie_mask"] = 255

        #Empty match
        flow["match"] = {}

        #Empty instructions
        flow["instructions"] = {"instruction": []}

        #  Wrap it in inventory
        flow = {"flow-node-inventory:flow": flow}

        return flow

    def _populate_flow_action_instruction(self, flow, action_list, apply_immediately):

        if apply_immediately:
            apply_actions_instruction = {"apply-actions": {"action": action_list}, "order": 0}
            flow["flow-node-inventory:flow"]["instructions"]["instruction"].append(apply_actions_instruction)
        else:
            write_actions_instruction = {"write-actions": {"action": action_list}, "order": 0}
            flow["flow-node-inventory:flow"]["instructions"]["instruction"].append(write_actions_instruction)


    def _push_table_miss_goto_next_table_flow(self, sw, table_id):

        # Create a lowest possible flow
        flow = self._create_base_flow(table_id, 0)

        #Compile instruction
        #  Assert that packet be sent to table with this table_id + 1
        go_to_table_instruction = {"go-to-table": {"table_id": table_id + 1}, "order": 0}

        flow["flow-node-inventory:flow"]["instructions"]["instruction"].append(go_to_table_instruction)

        self._push_flow(sw, flow)


    def _push_match_per_in_port_destination_instruct_group_flow(self, sw, table_id, group_id, priority,
                                                                flow_match, apply_immediately):

        flow = self._create_base_flow(table_id, priority)

        #Compile match
        flow["flow-node-inventory:flow"]["match"] = flow_match.generate_match_json(
            flow["flow-node-inventory:flow"]["match"])

        #Compile instruction

        #  Assert that group is executed upon match
        group_action = {"group-id": group_id}
        action_list = [{"group-action": group_action, "order": 0}]

        self._populate_flow_action_instruction(flow, action_list, apply_immediately)
        self._push_flow(sw, flow)

        return flow

    def _create_base_group(self):
        group = dict()

        self.group_id_cntr += 1
        group["group-id"] = str(self.group_id_cntr)
        group["barrier"] = False

        #  Empty Bucket List
        bucket = {"bucket": []}
        group["buckets"] = bucket
        group = {"flow-node-inventory:group": group}

        return group

    def _get_out_and_watch_port(self, intent):
        out_port = None
        watch_port = None

        if intent.in_port == intent.out_port:
            out_port = self.model.OFPP_IN
            watch_port = intent.out_port
        else:
            out_port = intent.out_port
            watch_port = intent.out_port

        return out_port, watch_port

    def _push_fast_failover_group(self, sw, primary_intent, failover_intent):

        group = self._create_base_group()
        bucket_list = group["flow-node-inventory:group"]["buckets"]["bucket"]
        group["flow-node-inventory:group"]["group-type"] = "group-ff"

        out_port, watch_port = self._get_out_and_watch_port(primary_intent)

        bucket_primary = {
            "action":[{'order': 0,
                       'output-action': {'output-node-connector': out_port}}],
            "bucket-id": 0,
            "watch_port": watch_port,
            "weight": 20}

        out_port, watch_port = self._get_out_and_watch_port(failover_intent)

        bucket_failover = {
            "action":[{'order': 0,
                       'output-action': {'output-node-connector': out_port}}],
            "bucket-id": 1,
            "watch_port": watch_port,
            "weight": 20}

        bucket_list.append(bucket_primary)
        bucket_list.append(bucket_failover)

        self._push_group(sw, group)

        return group

    def _push_select_all_group(self, sw, intent_list):

        group = self._create_base_group()
        bucket_list = group["flow-node-inventory:group"]["buckets"]["bucket"]
        group["flow-node-inventory:group"]["group-type"] = "group-all"

        if intent_list:
            for intent in intent_list:

                out_port, watch_port = self._get_out_and_watch_port(intent)

                bucket = {"action": [{'order': 0,
                                      'output-action': {'output-node-connector': out_port}}],
                          "bucket-id": 1}

                bucket_list.append(bucket)

        else:
            raise Exception("Need to have either one or two forwarding intents")

        self._push_group(sw, group)

        return group

    def _get_intents(self, dst_intents, intent_type):

        return_intent = []

        for intent in dst_intents:
            if intent.intent_type == intent_type:
                return_intent.append(intent)

        return return_intent

    def _push_mac_intent_flow(self, sw, mac_intent, table_id, priority):

        #sw, flow_match
        flow = self._create_base_flow(table_id, priority)

        #Compile match
        flow["flow-node-inventory:flow"]["match"] = mac_intent.flow_match.generate_match_json(
            flow["flow-node-inventory:flow"]["match"])

        #Compile instruction

        #  Assert that group is executed upon match
        output_action = {"output-node-connector": mac_intent.out_port}
        action_list = [{"output-action": output_action, "order": 0}]

        self._populate_flow_action_instruction(flow, action_list, mac_intent.apply_immediately)
        self._push_flow(sw, flow)

        return flow

    def push_host_mac_intents(self, sw, dst_intents):

        mac_intents = self._get_intents(dst_intents, "mac")
        if mac_intents:

            if len(mac_intents) > 1:
                if self.master_switch:
                    print "There are more than one mac intents for a single dst, will install only one"
                else:
                    raise Exception("Odd that there are more than one mac intents for a single dst")

            self._push_mac_intent_flow(sw, mac_intents[0], self.mac_forwarding_table_id, 1)

    def push_vlan_push_pop_intents(self, sw, dst_intents):

        push_vlan_intents = self._get_intents(dst_intents, "push_vlan")
        for push_vlan_intent in push_vlan_intents:
            flow = self._create_base_flow(self.vlan_rules_table_id, 1)

            #Compile match
            flow["flow-node-inventory:flow"]["match"] = push_vlan_intent.flow_match.generate_match_json(
                flow["flow-node-inventory:flow"]["match"])

            #Compile instruction
            action1 = {'order': 0, 'push-vlan-action': {"ethernet-type": 0x8100,
                                                        "vlan-id": push_vlan_intent.required_vlan_id}}

            set_vlan_id_action = {'vlan-match': {"vlan-id": {"vlan-id": push_vlan_intent.required_vlan_id,
                                                             "vlan-id-present": True}}}

            action2 = {'order': 1, 'set-field': set_vlan_id_action}

            action_list = [action1, action2]

            self._populate_flow_action_instruction(flow, action_list, push_vlan_intent.apply_immediately)

            # Also, punt such packets to the next table
            go_to_table_instruction = {"go-to-table": {"table_id": self.vlan_rules_table_id + 1}, "order": 1}
            flow["flow-node-inventory:flow"]["instructions"]["instruction"].append(go_to_table_instruction)

            self._push_flow(sw, flow)

        pop_vlan_intents = self._get_intents(dst_intents, "pop_vlan")
        for pop_vlan_intent in pop_vlan_intents:
            flow = self._create_base_flow(self.vlan_rules_table_id, 1)

            #Compile match
            flow["flow-node-inventory:flow"]["match"] = pop_vlan_intent.flow_match.generate_match_json(
                flow["flow-node-inventory:flow"]["match"])

            #Compile instruction
            pop_vlan_action = {}
            action_list = [{'order': 0, 'pop-vlan-action': pop_vlan_action}]

            self._populate_flow_action_instruction(flow, action_list, pop_vlan_intent.apply_immediately)

            # Also, punt such packets to the next table
            go_to_table_instruction = {"go-to-table": {"table_id": self.vlan_rules_table_id + 1}, "order": 1}
            flow["flow-node-inventory:flow"]["instructions"]["instruction"].append(go_to_table_instruction)

            self._push_flow(sw, flow)

    def trigger(self, affected_switches):

        for sw in affected_switches:

            print "-- Pushing at Switch:", sw

            # Push table miss entries at Table 0, 1, 2
            self._push_table_miss_goto_next_table_flow(sw, 0)
            self._push_table_miss_goto_next_table_flow(sw, 1)
            self._push_table_miss_goto_next_table_flow(sw, 2)

            intents = self.model.graph.node[sw]["sw"].intents

            for dst in intents:
                dst_intents = intents[dst]

                # Take care of mac intents for this destination
                self.push_host_mac_intents(sw, dst_intents)

                # Take care of vlan tag push/pop intents for this destination
                self.push_vlan_push_pop_intents(sw, dst_intents)

                primary_intent = None
                primary_intents = self._get_intents(dst_intents, "primary")
                if primary_intents:
                    primary_intent = primary_intents[0]

                reverse_intent = None
                reverse_intents = self._get_intents(dst_intents, "reverse")
                if reverse_intents:
                    reverse_intent = reverse_intents[0]

                balking_intent = None
                balking_intents = self._get_intents(dst_intents, "balking")
                if balking_intents:
                    balking_intent = balking_intents[0]

                failover_intent = None
                failover_intents = self._get_intents(dst_intents, "failover")
                if failover_intents:
                    failover_intent = failover_intents[0]

                #  Handle the case when the switch does not have to carry any failover traffic
                if primary_intent and not failover_intent:

                    group = self._push_select_all_group(sw, [primary_intent])

                    if not self.master_switch:
                        primary_intent.flow_match.set_match_field_element("in_port", int(primary_intent.in_port))

                    flow = self._push_match_per_in_port_destination_instruct_group_flow(
                        sw, self.ip_forwarding_table_id,
                        group["flow-node-inventory:group"]["group-id"],
                        1, primary_intent.flow_match, primary_intent.apply_immediately)

                if primary_intent and failover_intents:

                    #  See if both want same destination
                    if primary_intent.out_port != failover_intent.out_port:
                        group = self._push_fast_failover_group(sw, primary_intent, failover_intent)
                    else:
                        group = self._push_select_all_group(sw, [primary_intent])

                    # Push the rule that refers to the group
                    in_port = None
                    #Sanity check
                    if primary_intent.in_port != failover_intent.in_port:
                        #  This can only happen if the host is directly connected to the switch, so check that.
                        if not self.model.graph.has_edge(dst, sw):
                            raise Exception("Primary and failover intents' src port mismatch")
                    else:
                        in_port = primary_intent.in_port

                    primary_intent.flow_match.set_match_field_element("in_port", int(in_port))
                    flow = self._push_match_per_in_port_destination_instruct_group_flow(
                        sw, self.ip_forwarding_table_id,
                        group["flow-node-inventory:group"]["group-id"],
                        1, primary_intent.flow_match, primary_intent.apply_immediately)

                    if len(failover_intents) > 1:
#                        raise Exception ("Hitting an unexpected case.")
                        failover_intents = failover_intents[1:]

                #  Handle the case when switch only participates in carrying the failover traffic in-transit
                if not primary_intent and failover_intents:

                    for failover_intent in failover_intents:

                        group = self._push_select_all_group(sw, [failover_intent])
                        failover_intent.flow_match.set_match_field_element("in_port", int(failover_intent.in_port))
                        flow = self._push_match_per_in_port_destination_instruct_group_flow(
                            sw, self.ip_forwarding_table_id,
                            group["flow-node-inventory:group"]["group-id"],
                            1, failover_intent.flow_match, failover_intent.apply_immediately)

                if primary_intent and balking_intent:

                    group = self._push_fast_failover_group(sw, primary_intent, balking_intent)

                    in_port = None
                    #Sanity check
                    if primary_intent.in_port != balking_intent.in_port:
                        #  This can only happen if the host is directly connected to the switch, so check that.
                        if not self.model.graph.has_edge(dst, sw):
                            raise Exception("Primary and failover intents' src port mismatch")
                    else:
                        in_port = primary_intent.in_port

                    primary_intent.flow_match.set_match_field_element("in_port", int(in_port))
                    flow = self._push_match_per_in_port_destination_instruct_group_flow(
                        sw, self.ip_forwarding_table_id,
                        group["flow-node-inventory:group"]["group-id"],
                        1, primary_intent.flow_match, primary_intent.apply_immediately)

                if reverse_intent:

                    group = self._push_select_all_group(sw, [reverse_intent])
                    flow = self._push_match_per_in_port_destination_instruct_group_flow(
                        sw, self.reverse_rules_table_id,
                        group["flow-node-inventory:group"]["group-id"],
                        1, reverse_intent.flow_match, reverse_intent.apply_immediately)