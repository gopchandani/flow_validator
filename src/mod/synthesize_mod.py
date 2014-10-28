__author__ = 'Rakesh Kumar'

from model.model import Model
from synthesis.create_url import create_group_url, create_flow_url

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

    def _create_ethernet_match_group_apply_rule(self, flow_id, table_id, group_id):

        flow = dict()

        flow["flags"] = ""
        flow["table_id"] = table_id
        flow["id"] = str(flow_id)
        flow["priority"] = 1
        flow["idle-timeout"] = 0
        flow["hard-timeout"] = 0
        flow["cookie"] = flow_id
        flow["cookie_mask"] = 255

        #Compile match
        ethernet_type = {"type": str(0x0800)}
        ethernet_match = {"ethernet-type": ethernet_type}

        vlan_id = dict()
        vlan_id["vlan-id"] = 0
        vlan_id["vlan-id-present"] = False
        vlan_match = {"vlan-id": vlan_id}

        match = {"ethernet-match": ethernet_match}
        flow["match"] = match

        #Compile action
        group_action = {"group-id": group_id}
        action = {"group-action": group_action, "order": 0}
        apply_actions = {"action": action}
        instruction = {"apply-actions":apply_actions, "order": 0}
        instructions = {"instruction":instruction}
        flow["instructions"] = instructions

        #  Wrap it in inventory
        flow = {"flow-node-inventory:flow": flow}

        return flow

    def _create_vlan_match_group_apply_rule(self, flow_id, table_id, group_id, tag):

        flow = dict()

        #  Get a stock ethernet matching, group activating flow
        flow = self._create_ethernet_match_group_apply_rule(flow_id, table_id, group_id)

        #  Match on VLAN
        vlan_id = dict()
        vlan_id["vlan-id"] = tag
        vlan_id["vlan-id-present"] = True

        vlan_match = {"vlan-id": vlan_id}
        print vlan_match

        flow["flow-node-inventory:flow"]["match"]["vlan-match"] = vlan_match
        flow["flow-node-inventory:flow"]["priority"] = 2

        return flow

    def _create_mod_group(self, group_id, group_type, tag, port):

        group = dict()
        group["group-id"] = group_id
        group["group-type"] = group_type
        group["barrier"] = False

        #  Bucket
        actions = []

        action1 = {"action": [{'order': 0, 'push-vlan-action': {'ethernet-type': 0x8100}},
                              {'order': 1, 'set-field': {'vlan-match': {"vlan-id": {"vlan-id": tag, "vlan-id-present":True}}}},
                              {'order': 2, 'output-action': {'output-node-connector':port}}],
                   "bucket-id": 1, "watch_port": 3, "weight": 20}


        action2 = {"action": [{'order': 1, 'output-action': {'output-node-connector':port}}],
                   "bucket-id": 2, "watch_port": 1, "weight": 20}

        actions.append(action1)
        actions.append(action2)

        bucket = {"bucket": actions}
        group["buckets"] = bucket

        group = {"flow-node-inventory:group": group}

        return group

    def _push_change(self, url, pushed_content):

        resp, content = self.h.request(url, "PUT",
                                       headers={'Content-Type': 'application/json; charset=UTF-8'},
                                       body=json.dumps(pushed_content))

        print "Pushed:", pushed_content
        print resp, content
        time.sleep(0.5)


    def _populate_switch(self, node_id):

        table_id = 0
        flow_id = 1
        group_id = 7

        group = self._create_mod_group(group_id, "group-ff", "1234", self.OFPP_ALL)
        url = create_group_url(node_id, group_id)
        self._push_change(url, group)

        flow = self._create_ethernet_match_group_apply_rule(flow_id, table_id, group_id)
        url = create_flow_url(node_id, table_id, str(flow_id))
        self._push_change(url, flow)


        flow_id = 2
        group_id = 8

        group = self._create_mod_group(group_id, "group-ff", "1235", self.OFPP_IN)
        url = create_group_url(node_id, group_id)
        self._push_change(url, group)

        flow = self._create_vlan_match_group_apply_rule(flow_id, table_id, group_id, "1234")
        url = create_flow_url(node_id, table_id, str(flow_id))
        self._push_change(url, flow)


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

