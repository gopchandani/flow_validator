__author__ = 'Rakesh Kumar'

from model.model import Model
from synthesis.create_url import create_group_url, create_flow_url

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



    def _create_base_rule(self, flow_id, table_id, priority):

        flow = dict()

        flow["flags"] = ""
        flow["table_id"] = table_id
        flow["id"] = flow_id
        flow["priority"] = priority
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

    def _create_match_per_destination_instruct_group_rule(self, group_id, dst, priority):

        self.flow_id_cntr +=  1
        flow = self._create_base_rule(str(self.flow_id_cntr), 0, priority)

        #Compile match

        #  Assert that matching packets are of ethertype IP
        ethernet_type = {"type": str(0x0800)}
        ethernet_match = {"ethernet-type": ethernet_type}
        flow["flow-node-inventory:flow"]["match"]["ethernet-match"] = ethernet_match

        #  Assert that the destination should be dst
        flow["flow-node-inventory:flow"]["match"]["ipv4-destination"] = dst

        #Compile instruction

        #  Assert that group is executed upon match
        group_action = {"group-id": group_id}
        action = {"group-action": group_action, "order": 0}
        apply_action_instruction = {"apply-actions": {"action": action}, "order": 0}

        flow["flow-node-inventory:flow"]["instructions"]["instruction"].append(apply_action_instruction)

        return flow

    def _create_group_for_forwarding_intent(self, dst, forwarding_intents):

        group = dict()

        self.group_id_cntr += 1
        group["group-id"] = str(self.group_id_cntr)
        group["barrier"] = False

        #  Bucket
        bucket = None

        #  Need at least two of these to able to do a fast-failover style group
        if len(forwarding_intents) == 2:
            group["group-type"] = "group-ff"
            bucket_list = []
            for this_intent in forwarding_intents:
                bucket_id = None
                if this_intent["path_type"] == "primary":
                    bucket_id = 0
                if this_intent["path_type"] == "backup":
                    bucket_id = 1

                bucket = {
                    "action":[{'order': 0,
                               'output-action': {'output-node-connector':this_intent["departure_port"]}}],
                    "bucket-id": bucket_id,
                    "watch_port": this_intent["departure_port"],
                    "weight": 20}

                bucket_list.append(bucket)

            bucket = {"bucket": bucket_list}

        elif len(forwarding_intents) == 1:
            group["group-type"] = "group-all"

            bucket1 = {"action": [{'order': 0,
                                   'output-action': {'output-node-connector':forwarding_intents[0]["departure_port"]}}],
                       "bucket-id": 1}

            bucket_list =[bucket1]
            bucket = {"bucket": bucket_list}
        else:
             raise Exception("Need to have either one or two forwarding intents")

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
            forwarding_intent_dict = {"path_type": path_type,
                                      "arriving_port": arriving_port,
                                      "departure_port": departure_port}

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

    def dump_forwarding_intents(self):
        for sw in self.s:
            print "---", sw, "---"
            pprint.pprint(self.model.graph.node[sw]["forwarding_intents"])

    def push_switch_changes(self):

        for sw in self.s:

            for dst in self.model.graph.node[sw]["forwarding_intents"]:

                # Push the group
                group = self._create_group_for_forwarding_intent(dst,
                                                                 self.model.graph.node[sw]["forwarding_intents"][dst])
                group_id = group["flow-node-inventory:group"]["group-id"]
                url = create_group_url(sw, group_id)
                self._push_change(url, group)

                # Push the rule that refers to the group
                flow = self._create_match_per_destination_instruct_group_rule(group_id, dst, 1)
                flow_id = flow["flow-node-inventory:flow"]["id"]
                table_id = flow["flow-node-inventory:flow"]["table_id"]
                url = create_flow_url(sw, table_id, flow_id)
                self._push_change(url, flow)

    def synthesize_flow(self, src_host, dst_host):

        #  First find the shortest path between src and dst.
        p = nx.shortest_path(self.model.graph, source=src_host, target=dst_host)

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

