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

        self.group_id_cntr = 0

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

    def _create_group_for_forwarding_intent(self, dst, forwarding_intents):

        group = dict()

        self.group_id_cntr = self.group_id_cntr + 1
        group["group-id"] = self.group_id_cntr

        group["barrier"] = False

        #  Bucket
        bucket = None

        #  Need at least two of these to able to do a fast-failover style group
        if len(forwarding_intents) >= 2:
            group["group-type"] = "group-ff"

            bucket_candidate_1 = forwarding_intents[0]
            bucket_candidate_2 = forwarding_intents[1]

            bucket1 = {"action": [{'order': 0, 'output-action': {'output-node-connector':out_port}}],
                       "bucket-id": 1, "watch_port": 3, "weight": 20}

            bucket2 = {"action": [{'order': 0, 'output-action': {'output-node-connector':out_port}}],
                       "bucket-id": 2, "watch_port": 1, "weight": 20}

            bucket_list = [bucket1, bucket2]
            bucket = {"bucket": bucket_list}

        elif len(forwarding_intents) == 1:
            group["group-type"] = "group-all"

            bucket1 = {"action": [{'order': 0,
                                   'output-action': {'output-node-connector':forwarding_intents[0]["destination_port"]}}],
                       "bucket-id": 1, "watch_port": 3, "weight": 20}

            bucket_list =[bucket1]
            bucket = {"bucket": bucket_list}
        else:
             raise Exception("Need to have at least one forwarding intent")



        group["buckets"] = bucket

        group = {"flow-node-inventory:group": group}

        return group

    def _push_change(self, url, pushed_content):

        resp, content = self.h.request(url, "PUT",
                                       headers={'Content-Type': 'application/json; charset=UTF-8'},
                                       body=json.dumps(pushed_content))

        print "Pushed:", pushed_content.keys()[0], resp["status"]
        time.sleep(0.5)

    def get_forwarding_intents_dict(self, sw):

        forwarding_intents = None

        if "forwarding_intents" in self.model.graph.node[sw]:
            forwarding_intents = self.model.graph.node[sw]["forwarding_intents"]
        else:
            forwarding_intents = {}
            self.model.graph.node[sw]["forwarding_intents"] = forwarding_intents

        return forwarding_intents


    def _compute_path_forwarding_intents(self, p, s, switch_arriving_port=None):

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

            # Traffic leaves from the first switch's post
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
            s.add(p[i])

            #  Add the intent to the switch's node in the graph
            forwarding_intents = self.get_forwarding_intents_dict(p[i])
            forwarding_intent_dict = {"arriving_port": arriving_port, "departure_port": departure_port}

            if dst_host in forwarding_intents:
                forwarding_intents[dst_host].append(forwarding_intent_dict)
            else:
                forwarding_intents[dst_host] = [forwarding_intent_dict]

            # Prepare for next switch along the path if there is a next switch along the path
            if self.model.graph.node[p[i+1]]["node_type"] != "host":

                # Traffic arrives from the host to first switch at switch's port
                edge_ports_dict = self.model.graph[p[i]][p[i+1]]['edge_ports_dict']
                arriving_port = edge_ports_dict[p[i+1]]

                # Traffic leaves from the first switch's port
                edge_ports_dict = self.model.graph[p[i+1]][p[i+2]]['edge_ports_dict']
                departure_port = edge_ports_dict[p[i+1]]

    def _compute_backup_forwarding_intents(self, p, s):
        pass

    def _push_switch_changes(self, s):

        for sw in s:
            print sw
            print self.model.graph.node[sw]["forwarding_intents"]

            for dst in self.model.graph.node[sw]["forwarding_intents"]:
                #rule = self._create_rule_for_forwarding_intent()

                group = self._create_group_for_forwarding_intent(dst, self.model.graph.node[sw]["forwarding_intents"][dst])
                url = create_group_url(sw, group["flow-node-inventory:group"]["group-id"])
                self._push_change(url, group)


    def synthesize_flow(self, src_host, dst_host):

        # s represents the set of all switches that are
        # affected as a result of flow synthesis

        s = set()

        #  First find the shortest path between src and dst.
        p = nx.shortest_path(self.model.graph, source=src_host, target=dst_host)

        #  Compute all forwarding intents as a result of primary path
        self._compute_path_forwarding_intents(p, s)

        #  Along the shortest path, break a link one-by-one
        #  and accumulate desired action buckets in the resulting path


        #  For each switch in s, accumulate desired action buckets
        #  into a single group per destination and push the group and
        #  a single flow entry that matches anything destined for that group
        self._push_switch_changes(s)


def main():
    sm = SynthesizeDij()
    sm.synthesize_flow("10.0.0.1", "10.0.0.3")


if __name__ == "__main__":
    main()

