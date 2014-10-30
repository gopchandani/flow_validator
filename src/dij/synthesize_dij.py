__author__ = 'Rakesh Kumar'

from model.model import Model
from synthesis.create_url import create_group_url, create_flow_url

import httplib2
import json
import time
import sys
import networkx as nx



class SynthesizeDij():

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

    def _create_match_per_destination_instruct_group_rule(self, flow_id, table_id, group_id):

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

    def _create_group_with_multiple_action_buckets(self, group_id, out_port):

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

    def _push_change(self, url, pushed_content):

        resp, content = self.h.request(url, "PUT",
                                       headers={'Content-Type': 'application/json; charset=UTF-8'},
                                       body=json.dumps(pushed_content))

        print "Pushed:", pushed_content.keys()[0], resp["status"]
        time.sleep(0.5)

    def _push_switch_changes(self, s):
        pass

    def _compute_primary_forwarding_intents(self, p, s):
        pass

    def _compute_backup_forwarding_intents(self, p, s):
        pass

    def synthesize_flow(self, src_host, dst_host):

        # S represents the set of all switches that are 
        # affected as a result of flow synthesis

        s = set()

        #  First find the shortest path between src and dst.
        p = nx.shortest_path(self.model.graph, source=src_host, target=dst_host)

        print p

        #  Compute all forwarding intents as a result of primary path
        self._compute_primary_forwarding_intents(p, s)

        #  Along the shortest path, break a link one-by-one
        #  and accumulate desired action buckets in the resulting path


        #  For each switch in s, accumulate desired action buckets
        #  into a single group per destination and push the group and
        #  a single flow entry that matches anything destined for that group
        self._push_switch_changes(s)


def main():
    sm = SynthesizeDij()
    sm.synthesize_flow("10.0.0.1", "10.0.0.2")


if __name__ == "__main__":
    main()

