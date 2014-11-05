__author__ = 'Rakesh Kumar'

from model.model import Model

import httplib2
import json
import time
import sys



class SynthesizeMod():

    def __init__(self):

        self.OFPP_ALL = 0xfffffffc
        self.OFPP_IN = 0xfffffff8

        self.model = Model()
        self.h = httplib2.Http(".cache")
        self.h.add_credentials('admin', 'admin')

    def _create_base_rule(self, flow_id, table_id):

        flow = dict()

        flow["flags"] = ""
        flow["table_id"] = table_id
        flow["id"] = str(flow_id)
        flow["priority"] = 1
        flow["idle-timeout"] = 0
        flow["hard-timeout"] = 0
        flow["cookie"] = flow_id
        flow["cookie_mask"] = 255

        #Empty match
        flow["match"] = {}

        #Empty instructions
        flow["instructions"] = {"instruction": []}

        #  Wrap it in inventory
        flow = {"flow-node-inventory:flow": flow}

        return flow


    def _create_match_no_vlan_tag_instruct_group_rule(self, flow_id, table_id, group_id):

        flow = self._create_base_rule(flow_id, table_id)

        #Compile match

        #  Assert that matching packets are of ethertype IP
        ethernet_type = {"type": str(0x0800)}
        ethernet_match = {"ethernet-type": ethernet_type}
        flow["flow-node-inventory:flow"]["match"]["ethernet-match"] = ethernet_match

        #  Assert that matching packets have no VLAN tag on them
        vlan_id = dict()
        vlan_id["vlan-id"] = str(0)
        vlan_id["vlan-id-present"] = False
        vlan_match = {"vlan-id": vlan_id}

        flow["flow-node-inventory:flow"]["match"]["vlan-match"] = vlan_match

        #Compile instruction

        #  Assert that group is executed upon match
        group_action = {"group-id": group_id}
        action = {"group-action": group_action, "order": 0}
        apply_action_instruction = {"apply-actions": {"action": action}, "order": 0}

        flow["flow-node-inventory:flow"]["instructions"]["instruction"].append(apply_action_instruction)

        return flow


    def _create_match_vlan_tag_instruct_group_rule(self, flow_id, table_id, group_id, match_tag):

        flow = self._create_base_rule(flow_id, table_id)

        #Compile match

        #  Assert that matching packets are of ethertype IP
        ethernet_type = {"type": str(0x0800)}
        ethernet_match = {"ethernet-type": ethernet_type}
        flow["flow-node-inventory:flow"]["match"]["ethernet-match"] = ethernet_match

        #  Assert that matching packets have have specified VLAN tag on them
        vlan_id = dict()
        vlan_id["vlan-id"] = match_tag
        vlan_id["vlan-id-present"] = True
        vlan_match = {"vlan-id": vlan_id}

        flow["flow-node-inventory:flow"]["match"]["vlan-match"] = vlan_match

        #Compile instruction

        #  Assert that group is executed upon match
        group_action = {"group-id": group_id}
        action = {"group-action": group_action, "order": 0}
        apply_action_instruction = {"apply-actions": {"action": action}, "order": 0}

        flow["flow-node-inventory:flow"]["instructions"]["instruction"].append(apply_action_instruction)

        return flow

    def _create_match_no_vlan_tag_instruct_next_table_rule(self, flow_id, table_id, next_table_id):

        flow = self._create_base_rule(flow_id, table_id)

        #Compile match

        #  Assert that matching packets are of ethertype IP
        ethernet_type = {"type": str(0x0800)}
        ethernet_match = {"ethernet-type": ethernet_type}
        flow["flow-node-inventory:flow"]["match"]["ethernet-match"] = ethernet_match

        #  Assert that matching packets have no VLAN tag on them
        vlan_id = dict()
        vlan_id["vlan-id"] = str(0)
        vlan_id["vlan-id-present"] = False
        vlan_match = {"vlan-id": vlan_id}

        flow["flow-node-inventory:flow"]["match"]["vlan-match"] = vlan_match

        #Compile instruction

        go_to_table_instruction = {"go-to-table" : {"table_id": next_table_id}, "order": 1}
        flow["flow-node-inventory:flow"]["instructions"]["instruction"].append(go_to_table_instruction)

        return flow


    def _create_mod_group_with_outport(self, group_id, out_port):

        group = dict()
        group["group-id"] = group_id
        group["group-type"] = "group-ff"
        group["barrier"] = False

        #  Bucket
        actions = []

        action1 = {"action": [{'order': 0, 'output-action': {'output-node-connector':out_port}}],
                   "bucket-id": 1, "watch_port": 3, "weight": 20}

        action2 = {"action": [{'order': 0, 'output-action': {'output-node-connector':out_port}}],
                   "bucket-id": 2, "watch_port": 1, "weight": 20}

        actions.append(action1)
        actions.append(action2)

        bucket = {"bucket": actions}
        group["buckets"] = bucket

        group = {"flow-node-inventory:group": group}

        return group

    def _create_mod_group_with_vlan_tag_write(self, group_id, tag):

        group = dict()
        group["group-id"] = group_id
        group["group-type"] = "group-ff"
        group["barrier"] = False

        #  Bucket
        actions = []

        action1 = {"action": [{'order': 0, 'push-vlan-action': {'ethernet-type': 0x8100}},
                              {'order': 1, 'set-field': {'vlan-match': {"vlan-id": {"vlan-id": tag, "vlan-id-present":True}}}}],
                   "bucket-id": 1, "watch_port": 3, "weight": 20}


        action2 = {"action": [{'order': 0, 'push-vlan-action': {'ethernet-type': 0x8100}},
                              {'order': 1, 'set-field': {'vlan-match': {"vlan-id": {"vlan-id": tag, "vlan-id-present":True}}}}],
                   "bucket-id": 2, "watch_port": 1, "weight": 20}

        actions.append(action1)
        actions.append(action2)

        bucket = {"bucket": actions}
        group["buckets"] = bucket

        group = {"flow-node-inventory:group": group}

        return group

    def _create_mod_group_with_outport_and_vlan_tag_write(self, group_id, tag, port):

        group = dict()
        group["group-id"] = group_id
        group["group-type"] = "group-ff"
        group["barrier"] = False

        #  Bucket
        bucket_list = []

        bucket1 = {"action": [{'order': 0, 'push-vlan-action': {'ethernet-type': 0x8100}},
                              {'order': 1, 'set-field': {'vlan-match': {"vlan-id": {"vlan-id": tag, "vlan-id-present":True}}}},
                              {'order': 2, 'output-action': {'output-node-connector':port}}],
                   "bucket-id": 1, "watch_port": 3, "weight": 20}


        bucket2 = {"action": [{'order': 0, 'push-vlan-action': {'ethernet-type': 0x8100}},
                              {'order': 1, 'set-field': {'vlan-match': {"vlan-id": {"vlan-id": tag, "vlan-id-present":True}}}},
                              {'order': 2, 'output-action': {'output-node-connector':port}}],
                   "bucket-id": 2, "watch_port": 1, "weight": 20}

        bucket_list.append(bucket1)
        bucket_list.append(bucket2)

        bucket = {"bucket": bucket_list}
        group["buckets"] = bucket

        group = {"flow-node-inventory:group": group}

        return group


    def _push_change(self, url, pushed_content):

        resp, content = self.h.request(url, "PUT",
                                       headers={'Content-Type': 'application/json; charset=UTF-8'},
                                       body=json.dumps(pushed_content))

        print "Pushed:", pushed_content.keys()[0], resp["status"]
        time.sleep(0.5)


    def _populate_switch(self, node_id):

        #  S1 tags plain IP packets (with no vlan tags) with a vlan tag 1234 and sends them to ALL
        #  its neighbors, in this particular line case, there is just one guy called s2 that receives it

        if node_id == "openflow:1":

            #  Install the two groups for performing two separate functions
            group_id = 7
            group = self._create_mod_group_with_outport_and_vlan_tag_write(group_id, "1234", self.OFPP_ALL)
            url = create_group_url(node_id, group_id)
            self._push_change(url, group)


            #  Install the rule that invokes next table AND Calls out for a group
            table_id = 0
            flow_id = 1
            flow = self._create_match_no_vlan_tag_instruct_next_table_rule(flow_id, table_id, 1)
            url = create_flow_url(node_id, table_id, str(flow_id))
            self._push_change(url, flow)

            table_id = 1
            flow_id = 2
            flow = self._create_match_no_vlan_tag_instruct_group_rule(flow_id, table_id, 7)
            url = create_flow_url(node_id, table_id, str(flow_id))
            self._push_change(url, flow)


        # Switch s2 just sends the traffic with vlan tag 1234 back to s1
        if node_id == "openflow:2":

            table_id = 0
            flow_id = 1
            group_id = 8

            group = self._create_mod_group_with_outport_and_vlan_tag_write(group_id, "1235", self.OFPP_IN)
            url = create_group_url(node_id, group_id)
            self._push_change(url, group)

            flow = self._create_match_vlan_tag_instruct_group_rule(flow_id, table_id, group_id, "1234")
            url = create_flow_url(node_id, table_id, str(flow_id))
            self._push_change(url, flow)

        #  Switch s3 does not do nothing
        if node_id == "openflow:3":
            pass

    def trigger(self):

        #  First figure out what switches exist in the current topology
        #  Each switch needs the same thing (logically) inside it

        for n in self.model.graph.nodes():

            if self.model.graph.node[n]["node_type"] == "switch":
                print "We are in business here at n:", self.model.graph.node[n]["node_type"], n
                self._populate_switch(n)



def main():
    sm = SynthesizeMod()

    sm.trigger()

if __name__ == "__main__":
    main()

