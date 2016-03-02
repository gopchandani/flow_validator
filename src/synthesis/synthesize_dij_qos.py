__author__ = 'Rakesh Kumar'

from collections import defaultdict
from copy import deepcopy

import networkx as nx

from synthesis.synthesis_lib import SynthesisLib
from model.intent import Intent
from model.match import Match

class SynthesizeQoS():

    def __init__(self, network_graph, master_switch=False):

        self.network_graph = network_graph
        self.master_switch = master_switch

        self.synthesis_lib = SynthesisLib("localhost", "8181", self.network_graph)

        # s represents the set of all switches that are
        # affected as a result of flow synthesis
        self.s = set()
        
        self.primary_path_edges = []
        self.primary_path_edge_dict = {}

        self.apply_tag_intents_immediately = True
        self.apply_other_intents_immediately = True


        # Table contains the rules that drop packets destined to the same MAC address as host of origin
        self.loop_preventing_drop_table = 0

        # Table contains the reverse rules (they should be examined first)
        self.reverse_rules_table_id = 1

        # Table contains any rules that have to do with vlan tag push
        self.vlan_tag_push_rules_table_id = 2

        # Table contains any rules associated with forwarding host traffic
        self.mac_forwarding_table_id = 3

        # Table contains the actual forwarding rules
        self.ip_forwarding_table_id = 4

    def _compute_path_ip_intents(self, p, intent_type, flow_match, first_in_port, dst_switch_tag, min_rate, max_rate):

        edge_ports_dict = self.network_graph.get_edge_port_dict(p[0], p[1])
        
        in_port = first_in_port
        out_port = edge_ports_dict[p[0]]

        # This loop always starts at a switch
        for i in range(len(p) - 1):

            fwd_flow_match = deepcopy(flow_match)

            # All intents except the first one in the primary path must specify the vlan tag
            if not (i == 0 and intent_type == "primary"):
                fwd_flow_match["vlan_id"] = int(dst_switch_tag)

            intent = Intent(intent_type, fwd_flow_match, in_port, out_port,
                            self.apply_other_intents_immediately,
                            min_rate=min_rate, max_rate=max_rate)

            # Using dst_switch_tag as key here to
            # avoid adding multiple intents for the same destination

            self._add_intent(p[i], dst_switch_tag, intent)

            # Prep for next switch
            if i < len(p) - 2:
                edge_ports_dict = self.network_graph.get_edge_port_dict(p[i], p[i+1])
                in_port = edge_ports_dict[p[i+1]]

                edge_ports_dict = self.network_graph.get_edge_port_dict(p[i+1], p[i+2])
                out_port = edge_ports_dict[p[i+1]]

    def get_intents(self, dst_intents, intent_type):

        return_intent = []

        for intent in dst_intents:
            if intent.intent_type == intent_type:
                return_intent.append(intent)

        return return_intent

    def _add_intent(self, switch_id, key, intent):

        self.s.add(switch_id)
        intents = self.network_graph.graph.node[switch_id]["sw"].intents

        if key in intents:
            intents[key][intent] += 1
        else:
            intents[key] = defaultdict(int)
            intents[key][intent] = 1

    def _compute_destination_host_mac_intents(self, h_obj, flow_match, matching_tag, min_rate, max_rate):

        edge_ports_dict = self.network_graph.get_edge_port_dict(h_obj.switch_id, h_obj.node_id)
        out_port = edge_ports_dict[h_obj.switch_id]

        host_mac_match = deepcopy(flow_match)
        mac_int = int(h_obj.mac_addr.replace(":", ""), 16)
        host_mac_match["ethernet_destination"] = int(mac_int)
        host_mac_match["vlan_id"] = int(matching_tag)

        host_mac_intent = Intent("mac", host_mac_match, "all", out_port,
                                 self.apply_other_intents_immediately,
                                 min_rate=min_rate, max_rate=max_rate)

        # Avoiding addition of multiple mac forwarding intents for the same host 
        # by using its mac address as the key
        self._add_intent(h_obj.switch_id, h_obj.mac_addr, host_mac_intent)

    def _compute_push_vlan_tag_intents(self, h_obj, flow_match, required_tag):

        push_vlan_match= deepcopy(flow_match)
        push_vlan_match["in_port"] = int(h_obj.switch_port_attached)
        push_vlan_tag_intent = Intent("push_vlan", push_vlan_match, h_obj.switch_port_attached, "all",
                                      self.apply_tag_intents_immediately)

        push_vlan_tag_intent.required_vlan_id = required_tag

        # Avoiding adding a new intent for every departing flow for this switch,
        # by adding the tag as the key
        
        self._add_intent(h_obj.switch_id, required_tag, push_vlan_tag_intent)

    def synthesize_flow_qos(self, src_host, dst_host, flow_match, min_rate, max_rate):

        # Handy info
        edge_ports_dict = self.network_graph.get_edge_port_dict(src_host.node_id, src_host.switch_id)
        in_port = edge_ports_dict[src_host.switch_id]        
        dst_sw_obj = self.network_graph.get_node_object(dst_host.switch_id)
    
        ## Things at source
        # Tag packets leaving the source host with a vlan tag of the destination switch
        self._compute_push_vlan_tag_intents(src_host, flow_match, dst_sw_obj.synthesis_tag)    

        ## Things at destination
        # Add a MAC based forwarding rule for the destination host at the last hop
        self._compute_destination_host_mac_intents(dst_host, flow_match, dst_sw_obj.synthesis_tag, min_rate, max_rate)

        #  First find the shortest path between src and dst.
        p = nx.shortest_path(self.network_graph.graph, source=src_host.switch_id, target=dst_host.switch_id)
        print "Primary Path:", p

        self.primary_path_edge_dict[(src_host.node_id, dst_host.node_id)] = []

        for i in range(len(p)-1):

            if (p[i], p[i+1]) not in self.primary_path_edges and (p[i+1], p[i]) not in self.primary_path_edges:
                self.primary_path_edges.append((p[i], p[i+1]))

            self.primary_path_edge_dict[(src_host.node_id, dst_host.node_id)].append((p[i], p[i+1]))

        #  Compute all forwarding intents as a result of primary path
        self._compute_path_ip_intents(p, "primary", flow_match, in_port, dst_sw_obj.synthesis_tag, min_rate, max_rate)

    def push_switch_changes(self):

        for sw in self.s:

            print "-- Pushing at Switch:", sw

            # Push table miss entries at all Tables
            self.synthesis_lib.push_table_miss_goto_next_table_flow(sw, 0)
            self.synthesis_lib.push_table_miss_goto_next_table_flow(sw, 1)
            self.synthesis_lib.push_table_miss_goto_next_table_flow(sw, 2)
            self.synthesis_lib.push_table_miss_goto_next_table_flow(sw, 3)

            intents = self.network_graph.graph.node[sw]["sw"].intents

            for dst in intents:
                dst_intents = intents[dst]

                # Take care of mac intents for this destination
                self.synthesis_lib.push_destination_host_mac_intents(sw, dst_intents,
                                                                     self.get_intents(dst_intents, "mac"),
                                                                     self.mac_forwarding_table_id)

                # Take care of vlan tag push intents for this destination
                self.synthesis_lib.push_vlan_push_intents(sw, dst_intents,
                                                          self.get_intents(dst_intents, "push_vlan"),
                                                          self.vlan_tag_push_rules_table_id)

                primary_intents = self.get_intents(dst_intents, "primary")

                #  Handle the case when the switch does not have to carry any failover traffic
                if primary_intents:

                    group_id = self.synthesis_lib.push_select_all_group(sw, [primary_intents[0]])

                    if not self.master_switch:
                        primary_intents[0].flow_match["in_port"] = int(primary_intents[0].in_port)

                    flow = self.synthesis_lib.push_match_per_in_port_destination_instruct_group_flow(
                        sw,
                        self.ip_forwarding_table_id,
                        group_id,
                        1,
                        primary_intents[0].flow_match,
                        primary_intents[0].apply_immediately)

    def synthesize_all_node_pairs(self, rate):

        print "Synthesizing backup paths between all possible host pairs..."
        for src in self.network_graph.host_ids:
            for dst in self.network_graph.host_ids:

                # Ignore paths with same src/dst
                if src == dst:
                    continue

                src_h_obj = self.network_graph.get_node_object(src)
                dst_h_obj = self.network_graph.get_node_object(dst)

                # Ignore installation of paths between switches on the same switch
                if src_h_obj.switch_id == dst_h_obj.switch_id:
                    continue

                print "-----------------------------------------------------------------------------------------------"
                print 'Synthesizing primary and backup paths from', src, 'to', dst
                print "-----------------------------------------------------------------------------------------------"

                flow_match = Match(is_wildcard=True)
                flow_match["ethernet_type"] = 0x0800

                self.synthesize_flow_qos(src_h_obj, dst_h_obj, flow_match, rate, rate)
                print "-----------------------------------------------------------------------------------------------"

        self.push_switch_changes()
