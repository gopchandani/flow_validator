__author__ = 'Rakesh Kumar'

from model.model import Model
from synthesis.create_url import create_group_url, create_flow_url

from collections import defaultdict

import httplib2
import json
import time
import sys
import pprint
import networkx as nx

class SynthesizeDij():

    def __init__(self):

        self.OFPP_ALL = 0xfffffffc
        self.OFPP_IN = 0xfffffff8

        self.model = Model()

        self.group_id_cntr = 0
        self.flow_id_cntr = 0

        # s represents the set of all switches that are
        # affected as a result of flow synthesis
        self.s = set()

        self.h = httplib2.Http(".cache")
        self.h.add_credentials('admin', 'admin')



    def _create_base_rule(self, table_id, priority):

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

    def _create_match_per_src_port_destination_instruct_group_rule(self, group_id, src_port, dst, priority):

        flow = self._create_base_rule(0, priority)

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

    def _create_fast_failover_group(self, primary_intent, backup_intent):

        group = self._create_base_group()
        bucket_list = group["flow-node-inventory:group"]["buckets"]["bucket"]
        group["flow-node-inventory:group"]["group-type"] = "group-ff"

        bucket_primary = {
            "action":[{'order': 0,
                       'output-action': {'output-node-connector': primary_intent[2]}}],
            "bucket-id": 0,
            "watch_port": primary_intent[2],
            "weight": 20}

        bucket_backup = {
            "action":[{'order': 0,
                       'output-action': {'output-node-connector': backup_intent[2]}}],
            "bucket-id": 1,
            "watch_port": backup_intent[2],
            "weight": 20}

        bucket_list.append(bucket_primary)
        bucket_list.append(bucket_backup)

        return group


    def _create_select_all_group(self, intent_list):

        group = self._create_base_group()
        bucket_list = group["flow-node-inventory:group"]["buckets"]["bucket"]
        group["flow-node-inventory:group"]["group-type"] = "group-all"

        if intent_list:
            for intent in intent_list:
                bucket = {"action": [{'order': 0,
                                      'output-action': {'output-node-connector': intent[2]}}],
                          "bucket-id": 1}

                bucket_list.append(bucket)

        else:
            raise Exception("Need to have either one or two forwarding intents")

        return group


    def _push_change(self, url, pushed_content):

        resp, content = self.h.request(url, "PUT",
                                       headers={'Content-Type': 'application/json; charset=UTF-8'},
                                       body=json.dumps(pushed_content))

        if resp["status"] == "200":
            print "Pushed Successfully:", pushed_content.keys()[0], resp["status"]
        else:
            print "Problem Pushing:", pushed_content.keys()[0], "resp:", resp, "content:", content
            pprint.pprint(pushed_content)

        time.sleep(0.5)

    def get_forwarding_intents_dict(self, sw):

        forwarding_intents = None

        if "forwarding_intents" in self.model.graph.node[sw]:
            forwarding_intents = self.model.graph.node[sw]["forwarding_intents"]
        else:
            forwarding_intents = dict()
            self.model.graph.node[sw]["forwarding_intents"] = forwarding_intents

        return forwarding_intents

    def _compute_path_forwarding_intents(self, p, path_type, switch_arriving_port=None):

        dst_host = p[len(p) -1]

        edge_ports_dict = None
        departure_port = None
        arriving_port = None

        # Sanity check -- Check that last node of the p is a host, no matter what
        if self.model.graph.node[p[len(p) - 1]]["node_type"] != "host":
            raise Exception("The last node in the p has to be a host.")

        # Check whether the first node of path is a host or a switch.
        if self.model.graph.node[p[0]]["node_type"] == "host":

            #Traffic arrives from the host to first switch at switch's port
            edge_ports_dict = self.model.graph[p[0]][p[1]]['edge_ports_dict']
            arriving_port = edge_ports_dict[p[1]]

            # Traffic leaves from the first switch's port
            edge_ports_dict = self.model.graph[p[1]][p[2]]['edge_ports_dict']
            departure_port = edge_ports_dict[p[1]]

            p = p[1:]

        elif self.model.graph.node[p[0]]["node_type"] == "switch":
            if not switch_arriving_port:
                raise Exception("switching_arriving_port needed.")

            arriving_port = switch_arriving_port
            edge_ports_dict = self.model.graph[p[0]][p[1]]['edge_ports_dict']
            departure_port = edge_ports_dict[p[0]]

        # This look always starts at a switch
        for i in range(len(p) - 1):

            #  Add the switch to set S
            self.s.add(p[i])

            #  Add the intent to the switch's node in the graph
            forwarding_intents = self.get_forwarding_intents_dict(p[i])
            forwarding_intent = (path_type, arriving_port, departure_port)

            if dst_host in forwarding_intents:
                forwarding_intents[dst_host][forwarding_intent] += 1
            else:
                forwarding_intents[dst_host] = defaultdict(int)
                forwarding_intents[dst_host][forwarding_intent] = 1

            # Prepare for next switch along the path if there is a next switch along the path
            if self.model.graph.node[p[i+1]]["node_type"] != "host":

                # Traffic arrives from the host to first switch at switch's port
                edge_ports_dict = self.model.graph[p[i]][p[i+1]]['edge_ports_dict']
                arriving_port = edge_ports_dict[p[i+1]]

                # Traffic leaves from the first switch's port
                edge_ports_dict = self.model.graph[p[i+1]][p[i+2]]['edge_ports_dict']
                departure_port = edge_ports_dict[p[i+1]]

    def dump_forwarding_intents(self):
        for sw in self.s:
            print "---", sw, "---"
            pprint.pprint(self.model.graph.node[sw]["forwarding_intents"])

    def _identify_reverse_and_balking_intents(self, dst_intents):

        primary_exit_port = None
        for intent in dst_intents:
            if intent[0] == "primary":
                primary_exit_port = intent[2]
                break

        # Only back ups here, nothing to do
        if not primary_exit_port:
            return None



        addition_list = []
        deletion_list = []
        for intent in dst_intents:

            if intent[0] == "primary":
                continue

            #  If this intent is at a reverse flow carrier switch
            if intent[1] == primary_exit_port:

                # Add a new intent with modified key
                addition_list.append((("reverse", intent[1], self.OFPP_IN), dst_intents[intent]))
                deletion_list.append(intent)

            # If it is a blatant reversal on the very switch where reversal begins
            if intent[1] == intent[2]:

                # Add a new intent with modified key
                addition_list.append((("balking", intent[1], self.OFPP_IN), dst_intents[intent]))
                deletion_list.append(intent)


        for intent_key, intent_val in addition_list:
            dst_intents[intent_key] = intent_val

        for intent in deletion_list:
            del dst_intents[intent]

    def _get_intent(self, dst_intents, intent_type):
        return_intent = None
        for intent in dst_intents:
            if intent[0] == intent_type:
                return_intent = intent
                break
        return return_intent

    def push_switch_changes(self):

        for sw in self.s:

            for dst in self.model.graph.node[sw]["forwarding_intents"]:
                dst_intents = self.model.graph.node[sw]["forwarding_intents"][dst]
                self._identify_reverse_and_balking_intents(dst_intents)

                primary_intent = self._get_intent(dst_intents, "primary")
                backup_intent = self._get_intent(dst_intents, "backup")
                reverse_intent = self._get_intent(dst_intents, "reverse")
                balking_intent = self._get_intent(dst_intents, "balking")

                if primary_intent and backup_intent:

                    # Push the group
                    group = self._create_fast_failover_group(primary_intent, backup_intent)
                    group_id = group["flow-node-inventory:group"]["group-id"]
                    url = create_group_url(sw, group_id)
                    self._push_change(url, group)

                    # Push the rule that refers to the group
                    src_port = None

                    #Sanity check
                    if primary_intent[1] != backup_intent[1]:
                        #  This can only happen if the host is directly connected to the switch, so check that.
                        if not self.model.graph.has_edge(dst, sw):
                            raise Exception("Primary and Backup intents' src port mismatch")
                    else:
                        src_port = primary_intent[1]

                    flow = self._create_match_per_src_port_destination_instruct_group_rule(group_id, src_port, dst, 1)
                    flow_id = flow["flow-node-inventory:flow"]["id"]
                    table_id = flow["flow-node-inventory:flow"]["table_id"]
                    url = create_flow_url(sw, table_id, flow_id)
                    self._push_change(url, flow)

                if primary_intent and balking_intent:

                    # Push the group
                    group = self._create_fast_failover_group(primary_intent, balking_intent)
                    group_id = group["flow-node-inventory:group"]["group-id"]
                    url = create_group_url(sw, group_id)
                    self._push_change(url, group)

                    # Push the rule that refers to the group
                    src_port = None

                    #Sanity check
                    if primary_intent[1] != balking_intent[1]:
                        #  This can only happen if the host is directly connected to the switch, so check that.
                        if not self.model.graph.has_edge(dst, sw):
                            raise Exception("Primary and Backup intents' src port mismatch")
                    else:
                        src_port = primary_intent[1]

                    flow = self._create_match_per_src_port_destination_instruct_group_rule(group_id, src_port, dst, 1)
                    flow_id = flow["flow-node-inventory:flow"]["id"]
                    table_id = flow["flow-node-inventory:flow"]["table_id"]
                    url = create_flow_url(sw, table_id, flow_id)
                    self._push_change(url, flow)


                if not primary_intent and backup_intent:

                    # Push the group
                    group = self._create_select_all_group([backup_intent])
                    group_id = group["flow-node-inventory:group"]["group-id"]
                    url = create_group_url(sw, group_id)
                    self._push_change(url, group)

                    flow = self._create_match_per_src_port_destination_instruct_group_rule(group_id,
                                                                                           backup_intent[1], dst, 1)
                    flow_id = flow["flow-node-inventory:flow"]["id"]
                    table_id = flow["flow-node-inventory:flow"]["table_id"]
                    url = create_flow_url(sw, table_id, flow_id)
                    self._push_change(url, flow)

                if reverse_intent:

                    # Push the group
                    group = self._create_select_all_group([reverse_intent])
                    group_id = group["flow-node-inventory:group"]["group-id"]
                    url = create_group_url(sw, group_id)
                    self._push_change(url, group)

                    flow = self._create_match_per_src_port_destination_instruct_group_rule(group_id,
                                                                                           reverse_intent[1], dst, 2)
                    flow_id = flow["flow-node-inventory:flow"]["id"]
                    table_id = flow["flow-node-inventory:flow"]["table_id"]
                    url = create_flow_url(sw, table_id, flow_id)
                    self._push_change(url, flow)


    def synthesize_flow(self, src_host, dst_host):

        #  First find the shortest path between src and dst.
        p = nx.shortest_path(self.model.graph, source=src_host, target=dst_host)
        print p

        #  Compute all forwarding intents as a result of primary path
        self._compute_path_forwarding_intents(p, "primary")

        #  Along the shortest path, break a link one-by-one
        #  and accumulate desired action buckets in the resulting path
        edge_ports = self.model.graph[p[0]][p[1]]['edge_ports_dict']
        arriving_port = edge_ports[p[1]]

        #  Go through the path, one edge at a time
        for i in range(1, len(p) - 2):

            # Keep a copy of this handy
            edge_ports = self.model.graph[p[i]][p[i + 1]]['edge_ports_dict']

            # Delete the edge
            self.model.graph.remove_edge(p[i], p[i + 1])

            # Find the shortest path that results when the link breaks
            # and compute forwarding intents for that
            bp = nx.shortest_path(self.model.graph, source=p[i], target=dst_host)

            self._compute_path_forwarding_intents(bp, "backup", arriving_port)

            # Add the edge back and the data that goes along with it
            self.model.graph.add_edge(p[i], p[i + 1], edge_ports_dict=edge_ports)
            arriving_port = edge_ports[p[i+1]]


def main():
    sm = SynthesizeDij()
    sm.synthesize_flow("10.0.0.1", "10.0.0.4")
    sm.synthesize_flow("10.0.0.4", "10.0.0.1")
    sm.dump_forwarding_intents()
    sm.push_switch_changes()



if __name__ == "__main__":
    main()

