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

    def _compute_path_ip_intents(self, p, intent_type, flow_match, first_in_port, dst_switch_tag):

        edge_ports_dict = self.model.get_edge_port_dict(p[0], p[1])
        
        in_port = first_in_port
        out_port = edge_ports_dict[p[0]]

        # This loop always starts at a switch
        for i in range(len(p) - 1):

            intent = Intent(intent_type, flow_match, in_port, out_port)

            # Using dst_switch_tag as key here to
            # avoid adding multiple intents for the same destination

            self._add_intent(p[i], dst_switch_tag, intent)

            # Prep for next switch
            if i < len(p) - 2:
                edge_ports_dict = self.model.get_edge_port_dict(p[i], p[i+1])
                in_port = edge_ports_dict[p[i+1]]

                edge_ports_dict = self.model.get_edge_port_dict(p[i+1], p[i+2])
                out_port = edge_ports_dict[p[i+1]]

    def _get_intents(self, dst_intents, intent_type):

        return_intent = []

        for intent in dst_intents:
            if intent.intent_type == intent_type:
                return_intent.append(intent)

        return return_intent

    def _identify_reverse_and_balking_intents(self):

        for sw in self.s:

            intents = self.model.graph.node[sw]["sw"].intents

            for dst in intents:
                dst_intents = intents[dst]

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

    def _add_intent(self, switch_id, key, intent):

        self.s.add(switch_id)
        intents = self.model.graph.node[switch_id]["sw"].intents

        if key in intents:
            intents[key][intent] += 1
        else:
            intents[key] = defaultdict(int)
            intents[key][intent] = 1

    def _compute_destination_host_mac_intents(self, h_obj, flow_match):

        edge_ports_dict = self.model.get_edge_port_dict(h_obj.switch_id, h_obj.host_id)
        out_port = edge_ports_dict[h_obj.switch_id]

        host_mac_match = deepcopy(flow_match)
        host_mac_match.ethernet_destination = h_obj.mac_addr

        host_mac_intent = Intent("mac", host_mac_match, "all", out_port)

        # Avoiding addition of multiple mac forwarding intents for the same host 
        # by using its mac address as the key
        self._add_intent(h_obj.switch_id, h_obj.mac_addr, host_mac_intent)

    def _compute_push_vlan_tag_intents(self, h_obj, flow_match, required_tag):

        push_vlan_match= deepcopy(flow_match)
        push_vlan_match.in_port = h_obj.switch_port_attached
        push_vlan_tag_intent = Intent("push_vlan", push_vlan_match, h_obj.switch_port_attached, "all")
        push_vlan_tag_intent.required_vlan_id = required_tag

        # Avoiding adding a new intent for every departing flow for this switch,
        # by adding the tag itself as the key
        
        self._add_intent(h_obj.switch_id, required_tag, push_vlan_tag_intent)

    def _compute_pop_vlan_tag_intents(self, h_obj, flow_match, matching_tag):

        pop_vlan_match = deepcopy(flow_match)
        pop_vlan_match.vlan_id = matching_tag
        pop_vlan_tag_intent = Intent("pop_vlan", pop_vlan_match, "all", "all")

        # Avoiding adding a new intent for every arriving flow for this host
        #  at destination by using its mac_addr as key
        
        self._add_intent(h_obj.switch_id, h_obj.mac_addr, pop_vlan_tag_intent)


    def synthesize_flow(self, src_host, dst_host, flow_match):

        # Handy info
        
        edge_ports_dict = self.model.get_edge_port_dict(src_host.host_id, src_host.switch_id)
        in_port = edge_ports_dict[src_host.switch_id]        
        dst_sw_obj = self.model.get_node_object(dst_host.switch_id)
    
        ## Things at source
        # Tag packets leaving the source host with a vlan tag of the destination switch
        self._compute_push_vlan_tag_intents(src_host, flow_match, dst_sw_obj.synthesis_tag)    


        ## Things at destination
        # Add a MAC based forwarding rule for the destination host at the last hop
        self._compute_destination_host_mac_intents(dst_host, flow_match)
        
        # Untag packets if they belong to a host connected to the dst switch AND they match its tag
        self._compute_pop_vlan_tag_intents(dst_host, flow_match, dst_sw_obj.synthesis_tag)


        #  First find the shortest path between src and dst.
        p = nx.shortest_path(self.model.graph, source=src_host.switch_id, target=dst_host.switch_id)
        print "Primary Path:", p

        #  Compute all forwarding intents as a result of primary path
        self._compute_path_ip_intents(p, "primary", flow_match, in_port, dst_sw_obj.synthesis_tag)

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

            self._compute_path_ip_intents(bp, "failover", flow_match, in_port, dst_sw_obj.synthesis_tag)

            # Add the edge back and the data that goes along with it
            self.model.graph.add_edge(p[i], p[i + 1], edge_ports_dict=edge_ports_dict)
            in_port = edge_ports_dict[p[i+1]]

    def push_switch_changes(self):

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

