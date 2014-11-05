__author__ = 'Rakesh Kumar'


import pprint
import time
import httplib2
import json

from model.model import Model


class SynthesisLib():

    def __init__(self, controller_host, controller_port, model=None):

        self.OFPP_ALL = 0xfffffffc
        self.OFPP_IN = 0xfffffff8

        if not model:
            self.model = Model()
        else:
            self.model = model

        self.controller_host = controller_host
        self.controller_port = controller_port


        self.group_id_cntr = 0
        self.flow_id_cntr = 0

        self.h = httplib2.Http(".cache")
        self.h.add_credentials('admin', 'admin')

    def _push_change(self, url, pushed_content):

        time.sleep(0.1)

        resp, content = self.h.request(url, "PUT",
                                       headers={'Content-Type': 'application/json; charset=UTF-8'},
                                       body=json.dumps(pushed_content))

        # resp = {"status": "200"}
        pprint.pprint(pushed_content)

        if resp["status"] == "200":
            print "Pushed Successfully:", pushed_content.keys()[0], resp["status"]
        else:
            print "Problem Pushing:", pushed_content.keys()[0], "resp:", resp, "content:", content
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

    def _push_match_per_src_port_destination_instruct_group_flow(self, sw, group_id, src_port, dst, priority):

        flow = self._create_base_flow(0, priority)

        #Compile match

        #  Assert that matching packets are of ethertype IP
        ethernet_type = {"type": str(0x0800)}
        ethernet_match = {"ethernet-type": ethernet_type}
        flow["flow-node-inventory:flow"]["match"]["ethernet-match"] = ethernet_match

        #  If src_port is provided Assert in-port == src_port
        if src_port:
            flow["flow-node-inventory:flow"]["match"]["in-port"] = src_port

        #  Assert that the destination should be dst
        flow["flow-node-inventory:flow"]["match"]["ipv4-destination"] = dst

        #Compile instruction

        #  Assert that group is executed upon match
        group_action = {"group-id": group_id}
        action = {"group-action": group_action, "order": 0}
        apply_action_instruction = {"apply-actions": {"action": action}, "order": 0}

        flow["flow-node-inventory:flow"]["instructions"]["instruction"].append(apply_action_instruction)

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

        if intent[1] == intent[2]:
            out_port = self.OFPP_IN
            watch_port = intent[2]
        else:
            out_port = intent[2]
            watch_port = intent[2]

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
            if intent[0] == intent_type:
                return_intent.append(intent)

        return return_intent


    def trigger(self, affected_switches):

        for sw in affected_switches:

            print "-- Pushing at Switch:", sw

            for dst in self.model.graph.node[sw]["forwarding_intents"]:
                dst_intents = self.model.graph.node[sw]["forwarding_intents"][dst]

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
                    flow = self._push_match_per_src_port_destination_instruct_group_flow(sw,
                        group["flow-node-inventory:group"]["group-id"], primary_intent[1], dst, 1)

                if primary_intent and failover_intents:

                    #  See if both want same destination
                    if primary_intent[2] != failover_intent[2]:
                        group = self._push_fast_failover_group(sw, primary_intent, failover_intent)
                    else:
                        group = self._push_select_all_group(sw, [primary_intent])

                    # Push the rule that refers to the group
                    src_port = None
                    #Sanity check
                    if primary_intent[1] != failover_intent[1]:
                        #  This can only happen if the host is directly connected to the switch, so check that.
                        if not self.model.graph.has_edge(dst, sw):
                            raise Exception("Primary and failover intents' src port mismatch")
                    else:
                        src_port = primary_intent[1]

                    flow = self._push_match_per_src_port_destination_instruct_group_flow(sw,
                        group["flow-node-inventory:group"]["group-id"], src_port, dst, 1)

                    if len(failover_intents) > 1:
                        raise Exception ("Hitting an unexpected case.")
                        failover_intents = failover_intents[1:]

                #  Handle the case when switch only participates in carrying the failover traffic in-transit
                if not primary_intent and failover_intents:

                    for failover_intent in failover_intents:

                        group = self._push_select_all_group(sw, [failover_intent])
                        flow = self._push_match_per_src_port_destination_instruct_group_flow(sw,
                            group["flow-node-inventory:group"]["group-id"], failover_intent[1], dst, 1)

                if primary_intent and balking_intent:

                    group = self._push_fast_failover_group(sw, primary_intent, balking_intent)

                    src_port = None
                    #Sanity check
                    if primary_intent[1] != balking_intent[1]:
                        #  This can only happen if the host is directly connected to the switch, so check that.
                        if not self.model.graph.has_edge(dst, sw):
                            raise Exception("Primary and failover intents' src port mismatch")
                    else:
                        src_port = primary_intent[1]

                    flow = self._push_match_per_src_port_destination_instruct_group_flow(sw,
                        group["flow-node-inventory:group"]["group-id"], src_port, dst, 1)

                if reverse_intent:

                    group = self._push_select_all_group(sw, [reverse_intent])
                    flow = self._push_match_per_src_port_destination_instruct_group_flow(sw,
                        group["flow-node-inventory:group"]["group-id"], reverse_intent[1], dst, 2)
