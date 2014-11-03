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

    def _push_change(self, url, pushed_content):

        time.sleep(0.5)

        resp, content = self.h.request(url, "PUT",
                                       headers={'Content-Type': 'application/json; charset=UTF-8'},
                                       body=json.dumps(pushed_content))

        # resp = {"status": "200"}
        # pprint.pprint(pushed_content)

        if resp["status"] == "200":
            print "Pushed Successfully:", pushed_content.keys()[0], resp["status"]
        else:
            print "Problem Pushing:", pushed_content.keys()[0], "resp:", resp, "content:", content
            pprint.pprint(pushed_content)


    def _push_flow(self, sw, flow):
        
        flow_id = flow["flow-node-inventory:flow"]["id"]
        table_id = flow["flow-node-inventory:flow"]["table_id"]
        url = create_flow_url(sw, table_id, flow_id)
        self._push_change(url, flow)

    def _push_group(self, sw, group):
        
        group_id = group["flow-node-inventory:group"]["group-id"]
        url = create_group_url(sw, group_id)
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


    def get_forwarding_intents_dict(self, sw):

        forwarding_intents = None

        if "forwarding_intents" in self.model.graph.node[sw]:
            forwarding_intents = self.model.graph.node[sw]["forwarding_intents"]
        else:
            forwarding_intents = dict()
            self.model.graph.node[sw]["forwarding_intents"] = forwarding_intents

        return forwarding_intents

    def _compute_path_forwarding_intents(self, p, path_type, switch_arriving_port=None):

        src_node = p[0]
        dst_node = p[len(p) -1]

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

            if dst_node in forwarding_intents:
                forwarding_intents[dst_node][forwarding_intent] += 1
            else:
                forwarding_intents[dst_node] = defaultdict(int)
                forwarding_intents[dst_node][forwarding_intent] = 1

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

            for port in self.model.graph.node[sw]["ports"]:
                print self.model.graph.node[sw]["ports"][port]

            pprint.pprint(self.model.graph.node[sw]["forwarding_intents"])

    def _get_intent(self, dst_intents, intent_type):
        return_intent = None
        for intent in dst_intents:
            if intent[0] == intent_type:
                return_intent = intent
                break
        return return_intent

    def _identify_reverse_and_balking_intents(self):

        for sw in self.s:

            for dst in self.model.graph.node[sw]["forwarding_intents"]:
                dst_intents = self.model.graph.node[sw]["forwarding_intents"][dst]
                primary_intent = self._get_intent(dst_intents, "primary")
                addition_list = []
                deletion_list = []

                for intent in dst_intents:

                    #  Nothing needs to be done for primary intent
                    if intent == primary_intent:
                        continue

                    # A balking intent happens on the switch where reversal begins,
                    # it is characterized by the fact that the traffic exits the same port where it came from
                    if intent[1] == intent[2]:
                        # Add a new intent with modified key
                        addition_list.append((("balking", intent[1], intent[2]), dst_intents[intent]))
                        deletion_list.append(intent)
                        continue

                    #  Processing from this point onwards require presence of a primary intent
                    if not primary_intent:
                        continue

                    #  If this intent is at a reverse flow carrier switch

                    #  There are two ways to identify reverse intents
                    #  Both cases need a separate rule at a higher priority handling it

                    #  1. at the source switch, with intent's source port equal to destination port of the primary intent
                    if intent[1] == primary_intent[2]:
                        # Add a new intent with modified key
                        addition_list.append((("reverse", intent[1], intent[2]), dst_intents[intent]))
                        deletion_list.append(intent)

                    #  2. At the intermediate switch (not where reversal begins),
                    # with intent's destination port equal to source port of primary intent
                    if intent[2] == primary_intent[1]:
                        # Add a new intent with modified key
                        addition_list.append((("reverse", intent[1], intent[2]), dst_intents[intent]))
                        deletion_list.append(intent)

                for intent_key, intent_val in addition_list:
                    dst_intents[intent_key] = intent_val

                for intent in deletion_list:

                    #  To handle the cases when the intent falls under multiple categories
                    if intent in dst_intents:
                        del dst_intents[intent]

    def push_switch_changes(self):

        for sw in self.s:

            print "-- Pushing at Switch:", sw

            for dst in self.model.graph.node[sw]["forwarding_intents"]:
                dst_intents = self.model.graph.node[sw]["forwarding_intents"][dst]
                primary_intent = self._get_intent(dst_intents, "primary")
                failover_intent = self._get_intent(dst_intents, "failover")
                reverse_intent = self._get_intent(dst_intents, "reverse")
                balking_intent = self._get_intent(dst_intents, "balking")

                if primary_intent and failover_intent:

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

                if not primary_intent and failover_intent:

                    group = self._push_select_all_group(sw, [failover_intent])
                    flow = self._push_match_per_src_port_destination_instruct_group_flow(sw,
                        group["flow-node-inventory:group"]["group-id"], failover_intent[1], dst, 1)

                if reverse_intent:

                    group = self._push_select_all_group(sw, [reverse_intent])
                    flow = self._push_match_per_src_port_destination_instruct_group_flow(sw,
                        group["flow-node-inventory:group"]["group-id"], reverse_intent[1], dst, 2)

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

            self._compute_path_forwarding_intents(bp, "failover", arriving_port)

            # Add the edge back and the data that goes along with it
            self.model.graph.add_edge(p[i], p[i + 1], edge_ports_dict=edge_ports)
            arriving_port = edge_ports[p[i+1]]

def main():
    sm = SynthesizeDij()

    sm.synthesize_flow("10.0.0.1", "10.0.0.2")
    sm.synthesize_flow("10.0.0.2", "10.0.0.1")

    sm.dump_forwarding_intents()
    sm._identify_reverse_and_balking_intents()
    sm.dump_forwarding_intents()

    sm.push_switch_changes()


if __name__ == "__main__":
    main()

