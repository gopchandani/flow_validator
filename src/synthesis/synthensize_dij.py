
__author__ = 'Rakesh Kumar'

from model.model import Model
from model.match import Match

from synthesis.synthesis_lib import SynthesisLib
from synthesis.intent import Intent

from collections import defaultdict
from copy import deepcopy


import pprint
import networkx as nx


class SynthesizeDij():

    def __init__(self):

        self.model = Model()
        self.synthesis_lib = SynthesisLib("localhost", "8181", self.model)

        # s represents the set of all switches that are
        # affected as a result of flow synthesis
        self.s = set()

    def _compute_path_ip_forwarding_intents(self, dst_ip_addr, p, intent_type, flow_match, switch_in_port):

        edge_ports_dict = self.model.get_edge_port_dict(p[0], p[1])
        switch_out_port = edge_ports_dict[p[0]]

        # This loop always starts at a switch
        for i in range(len(p) - 1):

            forwarding_intent = Intent(intent_type, flow_match, switch_in_port, switch_out_port)
            self._add_forwarding_intent(p[i], dst_ip_addr, forwarding_intent)


            # Prep for next switch
            if i < len(p) - 2:
                edge_ports_dict = self.model.get_edge_port_dict(p[i], p[i+1])
                switch_in_port = edge_ports_dict[p[i+1]]

                edge_ports_dict = self.model.get_edge_port_dict(p[i+1], p[i+2])
                switch_out_port = edge_ports_dict[p[i+1]]

    def _get_intents(self, dst_intents, intent_type):

        return_intent = []

        for intent in dst_intents:
            if intent.intent_type == intent_type:
                return_intent.append(intent)

        return return_intent

    def _identify_reverse_and_balking_intents(self):

        for sw in self.s:

            forwarding_intents = self.model.graph.node[sw]["sw"].forwarding_intents

            for dst in forwarding_intents:
                dst_intents = forwarding_intents[dst]

                # Assume that there is always one primary intent
                primary_intent = None
                primary_intents = self._get_intents(dst_intents, "primary")
                if primary_intents:
                    primary_intent = primary_intents[0]

                for intent in dst_intents:

                    #  Nothing needs to be done for primary intent
                    if intent == primary_intent:
                        continue

                    # A balking intent happens on the switch where reversal begins,
                    # it is characterized by the fact that the traffic exits the same port where it came from
                    if intent.in_port == intent.out_port:

                        # Add a new intent with modified key
                        intent.intent_type = "balking"
                        continue

                    #  Processing from this point onwards require presence of a primary intent
                    if not primary_intent:
                        continue

                    #  If this intent is at a reverse flow carrier switch

                    #  There are two ways to identify reverse intents

                    #  1. at the source switch, with intent's source port equal to destination port of the primary intent
                    if intent.in_port == primary_intent.out_port:
                        intent.intent_type = "reverse"
                        continue

                    #  2. At any other switch
                    # with intent's destination port equal to source port of primary intent
                    if intent.out_port == primary_intent.in_port:
                        intent.intent_type = "reverse"
                        continue

    def _add_forwarding_intent(self, switch_id, key, forwarding_intent):

        self.s.add(switch_id)
        forwarding_intents = self.model.graph.node[switch_id]["sw"].forwarding_intents

        if key in forwarding_intents:
            forwarding_intents[key][forwarding_intent] += 1
        else:
            forwarding_intents[key] = defaultdict(int)
            forwarding_intents[key][forwarding_intent] = 1

    def _compute_destination_host_mac_forwarding_intents(self, dst_host, flow_match):

        edge_ports_dict = self.model.get_edge_port_dict(dst_host.switch_id, dst_host.host_id)
        switch_out_port = edge_ports_dict[dst_host.switch_id]

        flow_match_with_dst_mac = deepcopy(flow_match)
        flow_match_with_dst_mac.ethernet_destination = dst_host.mac_addr

        forwarding_intent = Intent("mac", flow_match_with_dst_mac, "all", switch_out_port)

        self._add_forwarding_intent(dst_host.switch_id, dst_host.mac_addr, forwarding_intent)

    def _compute_push_pop_vlan_tag_intents(self, flow_match=None):

        if not flow_match:
            flow_match = Match()

        for sw in self.s:
            sw_obj = self.model.get_node_object(sw)
            print sw, sw_obj.synthesis_tag

            for port in sw_obj.ports:
                if sw_obj.ports[port].faces == "host":
                    
                    # Every packet that comes from a host needs to be attached with a vlan tag
                    push_vlan_match = deepcopy(flow_match)
                    push_vlan_match.vlan_id = sw_obj.synthesis_tag
                    push_vlan_tag_intent = Intent("push_vlan", push_vlan_match, sw_obj.ports[port].port_number, "all")

                    # Every packet that is destined to a host needs to be stripped off of the vlan tag
                    pop_vlan_match = deepcopy(flow_match)
                    pop_vlan_match.vlan_id = sw_obj.synthesis_tag
                    pop_vlan_tag_intent = Intent("pop_vlan", pop_vlan_match, "all", sw_obj.ports[port].port_number)



    def synthesize_flow(self, src_host, dst_host, flow_match):

        self._compute_destination_host_mac_forwarding_intents(dst_host, flow_match)

        edge_ports_dict = self.model.get_edge_port_dict(src_host.host_id, src_host.switch_id)
        switch_in_port = edge_ports_dict[src_host.switch_id]

        #  First find the shortest path between src and dst.
        p = nx.shortest_path(self.model.graph, source=src_host.switch_id, target=dst_host.switch_id)
        print "Primary Path:", p

        #  Compute all forwarding intents as a result of primary path
        self._compute_path_ip_forwarding_intents(dst_host.host_id, p, "primary", flow_match, switch_in_port)

        #  Along the shortest path, break a link one-by-one
        #  and accumulate desired action buckets in the resulting path

        #  Go through the path, one edge at a time
        for i in range(len(p) - 1):

            # Keep a copy of this handy
            edge_ports_dict = self.model.get_edge_port_dict(p[i], p[i+1])

            # Delete the edge
            self.model.graph.remove_edge(p[i], p[i + 1])

            # Find the shortest path that results when the link breaks
            # and compute forwarding intents for that
            bp = nx.shortest_path(self.model.graph, source=p[i], target=dst_host.switch_id)
            print "Backup Path", bp

            self._compute_path_ip_forwarding_intents(dst_host.host_id, bp, "failover", flow_match, switch_in_port)

            # Add the edge back and the data that goes along with it
            self.model.graph.add_edge(p[i], p[i + 1], edge_ports_dict=edge_ports_dict)
            switch_in_port = edge_ports_dict[p[i+1]]


    def push_switch_changes(self):

        #  Before it all goes to the switches, ensure that the packets get vlan tagged/un-tagged
        # TODO: Pass a legit flow match here
        self._compute_push_pop_vlan_tag_intents()

        self.synthesis_lib.trigger(self.s)

    def synthesize_all_node_pairs(self):

        print "Synthesizing backup paths between all possible host pairs..."
        for src in self.model.get_host_ids():
            for dst in self.model.get_host_ids():

                # Ignore paths with same src/dst
                if src == dst:
                    continue

                print "--------------------------------------------------------------------------------------------------------"
                print 'Synthesizing primary and backup paths from', src, 'to', dst
                print "--------------------------------------------------------------------------------------------------------"

                flow_match = Match()
                #flow_match.udp_destination_port = 80
                flow_match.ethernet_type = 0x0800
                flow_match.dst_ip_addr = self.model.graph.node[dst]["h"].ip_addr

                self.synthesize_flow(self.model.get_node_object(src), self.model.get_node_object(dst), flow_match)

                print "--------------------------------------------------------------------------------------------------------"


        self._identify_reverse_and_balking_intents()
        self.push_switch_changes()

def main():
    sm = SynthesizeDij()
    sm.synthesize_all_node_pairs()

if __name__ == "__main__":
    main()

