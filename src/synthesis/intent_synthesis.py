__author__ = 'Rakesh Kumar'

import networkx as nx


from collections import defaultdict
from copy import deepcopy


from model.network_graph import NetworkGraph
from synthesis.synthesis_lib import SynthesisLib
from model.intent import Intent
from model.match import Match

class IntentSynthesis():

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
        self.apply_other_intents_immediately = False

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

    def _compute_path_ip_intents(self, p, intent_type, flow_match, first_in_port, dst_switch_tag):

        edge_ports_dict = self.network_graph.get_edge_port_dict(p[0], p[1])
        
        in_port = first_in_port
        out_port = edge_ports_dict[p[0]]

        # This loop always starts at a switch
        for i in range(len(p) - 1):

            fwd_flow_match = deepcopy(flow_match)

            # All intents except the first one in the primary path must specify the vlan tag
            if not (i == 0 and intent_type == "primary"):
                fwd_flow_match["vlan_id"] = int(dst_switch_tag)

            if in_port == out_port:
                pass

            intent = Intent(intent_type, fwd_flow_match, in_port, out_port)

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

    def _identify_reverse_and_balking_intents(self):

        for sw in self.s:

            intents = self.network_graph.graph.node[sw]["sw"].intents

            for dst in intents:
                dst_intents = intents[dst]

                primary_intent = None
                primary_intents = self.get_intents(dst_intents, "primary")
                if primary_intents:
                    primary_intent = primary_intents[0]

                for intent in dst_intents:

                    #  Nothing needs to be done for primary intent
                    if intent == primary_intent:
                        continue

                    # Nothing needs to be done for vlan intents either
                    if intent.intent_type == "push_vlan":
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
        intents = self.network_graph.graph.node[switch_id]["sw"].intents

        if key in intents:
            intents[key][intent] += 1
        else:
            intents[key] = defaultdict(int)
            intents[key][intent] = 1


    def _compute_destination_host_mac_intents(self, h_obj, flow_match, matching_tag):

        edge_ports_dict = self.network_graph.get_edge_port_dict(h_obj.switch_id, h_obj.node_id)
        out_port = edge_ports_dict[h_obj.switch_id]

        host_mac_match = deepcopy(flow_match)
        mac_int = int(h_obj.mac_addr.replace(":", ""), 16)
        host_mac_match["ethernet_destination"] = int(mac_int)
        host_mac_match["vlan_id"] = int(matching_tag)

        host_mac_intent = Intent("mac", host_mac_match, "all", out_port, apply_immediately=False)

        # Avoiding addition of multiple mac forwarding intents for the same host 
        # by using its mac address as the key
        self._add_intent(h_obj.switch_id, h_obj.mac_addr, host_mac_intent)

    def _compute_push_vlan_tag_intents(self, h_obj, flow_match, required_tag):

        push_vlan_match= deepcopy(flow_match)
        push_vlan_match["in_port"] = int(h_obj.switch_port_attached)
        push_vlan_tag_intent = Intent("push_vlan", push_vlan_match, h_obj.switch_port_attached, "all", apply_immediately=False)
        push_vlan_tag_intent.required_vlan_id = required_tag

        # Avoiding adding a new intent for every departing flow for this switch,
        # by adding the tag as the key
        
        self._add_intent(h_obj.switch_id, required_tag, push_vlan_tag_intent)

    def synthesize_flow(self, src_host, dst_host, flow_match):

        # Handy info
        edge_ports_dict = self.network_graph.get_edge_port_dict(src_host.node_id, src_host.switch_id)
        in_port = edge_ports_dict[src_host.switch_id]        
        dst_sw_obj = self.network_graph.get_node_object(dst_host.switch_id)
    
        ## Things at source
        # Tag packets leaving the source host with a vlan tag of the destination switch
        self._compute_push_vlan_tag_intents(src_host, flow_match, dst_sw_obj.synthesis_tag)    

        ## Things at destination
        # Add a MAC based forwarding rule for the destination host at the last hop
        self._compute_destination_host_mac_intents(dst_host, flow_match, dst_sw_obj.synthesis_tag)

        #  First find the shortest path between src and dst.
        p = nx.shortest_path(self.network_graph.graph, source=src_host.switch_id, target=dst_host.switch_id)
        print "Primary Path:", p

        self.primary_path_edge_dict[(src_host.node_id, dst_host.node_id)] = []

        for i in range(len(p)-1):

            if (p[i], p[i+1]) not in self.primary_path_edges and (p[i+1], p[i]) not in self.primary_path_edges:
                self.primary_path_edges.append((p[i], p[i+1]))

            self.primary_path_edge_dict[(src_host.node_id, dst_host.node_id)].append((p[i], p[i+1]))


        #  Compute all forwarding intents as a result of primary path
        self._compute_path_ip_intents(p, "primary", flow_match, in_port, dst_sw_obj.synthesis_tag)

        #  Along the shortest path, break a link one-by-one
        #  and accumulate desired action buckets in the resulting path

        #  Go through the path, one edge at a time
        for i in range(len(p) - 1):

            # Keep a copy of this handy
            edge_ports_dict = self.network_graph.get_edge_port_dict(p[i], p[i+1])

            # Delete the edge
            self.network_graph.graph.remove_edge(p[i], p[i + 1])

            # Find the shortest path that results when the link breaks
            # and compute forwarding intents for that
            try:
                bp = nx.shortest_path(self.network_graph.graph, source=p[i], target=dst_host.switch_id)
                print "Backup Path", bp

                self._compute_path_ip_intents(bp, "failover", flow_match, in_port, dst_sw_obj.synthesis_tag)
            except nx.exception.NetworkXNoPath:
                print "No backup path between:", p[i], "to:", dst_host.switch_id

            # Add the edge back and the data that goes along with it
            self.network_graph.graph.add_edge(p[i], p[i + 1], edge_ports_dict=edge_ports_dict)
            in_port = edge_ports_dict[p[i+1]]

    def push_switch_changes(self):

        for sw in self.s:

            print "-- Pushing at Switch:", sw

            # Push rules at the switch that drop packets from hosts that are connected to the switch
            # and have the same MAC address as originating hosts
            self.synthesis_lib.push_loop_preventing_drop_rules(sw, self.loop_preventing_drop_table)

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
                reverse_intents = self.get_intents(dst_intents, "reverse")
                balking_intents = self.get_intents(dst_intents, "balking")
                failover_intents = self.get_intents(dst_intents, "failover")

                #  Handle the case when the switch does not have to carry any failover traffic
                if primary_intents and not failover_intents:

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

                if primary_intents and failover_intents:

                    # TODO: All of the intents in both list should want the same port
                    #  See if both want same destination port of out of this switch
                    if primary_intents[0].out_port != failover_intents[0].out_port:
                        group_id = self.synthesis_lib.push_fast_failover_group(sw, primary_intents[0], failover_intents[0])
                    else:
                        raise Exception("Something is wrong with installed intents.")

                    # Push the rule that refers to the group

                    primary_intents[0].flow_match["vlan_id"] = int(dst)

                    flow = self.synthesis_lib.push_match_per_in_port_destination_instruct_group_flow(
                        sw,
                        self.ip_forwarding_table_id,
                        group_id,
                        1,
                        primary_intents[0].flow_match,
                        primary_intents[0].apply_immediately)

                #  Handle the case when switch only participates in carrying the failover traffic in-transit
                if not primary_intents and failover_intents:

                    for failover_intent in failover_intents:

                        group_id = self.synthesis_lib.push_select_all_group(sw, [failover_intent])
                        failover_intent.flow_match["in_port"] = int(failover_intent.in_port)
                        flow = self.synthesis_lib.push_match_per_in_port_destination_instruct_group_flow(
                            sw,
                            self.ip_forwarding_table_id,
                            group_id,
                            1,
                            failover_intent.flow_match,
                            failover_intent.apply_immediately)

                if primary_intents and balking_intents:

                    group_id = self.synthesis_lib.push_fast_failover_group(sw, primary_intents[0], balking_intents[0])
                    in_port = None

                    #Sanity check
                    if primary_intents[0].in_port != balking_intents[0].in_port:

                        #  This can only happen if the host is directly connected to the switch, so check that.
                        sw_obj = self.network_graph.get_node_object(sw)
                        if not int(sw_obj.synthesis_tag) == int(dst):
                            raise Exception("Primary and balking intents' src port mismatch")

                    else:
                        in_port = primary_intents[0].in_port

                    primary_intents[0].flow_match["in_port"] = int(in_port)
                    flow = self.synthesis_lib.push_match_per_in_port_destination_instruct_group_flow(
                        sw,
                        self.ip_forwarding_table_id,
                        group_id,
                        1,
                        primary_intents[0].flow_match,
                        primary_intents[0].apply_immediately)

                if reverse_intents:

                    group_id = self.synthesis_lib.push_select_all_group(sw, [reverse_intents[0]])

                    reverse_intents[0].flow_match["in_port"] = int(reverse_intents[0].in_port)
                    reverse_intents[0].flow_match["vlan_id"] = int(dst)

                    flow = self.synthesis_lib.push_match_per_in_port_destination_instruct_group_flow(
                        sw,
                        self.reverse_rules_table_id,
                        group_id,
                        1,
                        reverse_intents[0].flow_match,
                        reverse_intents[0].apply_immediately)


    def synthesize_all_node_pairs(self):

        print "Synthesizing backup paths between all possible host pairs..."
        for src in self.network_graph.get_experiment_host_ids():
            for dst in self.network_graph.get_experiment_host_ids():

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

                self.synthesize_flow(src_h_obj, dst_h_obj, flow_match)
                print "-----------------------------------------------------------------------------------------------"

        self._identify_reverse_and_balking_intents()
        self.push_switch_changes()

def main():
    ng = NetworkGraph()
    s = SynthesizeDij(ng)
    s.synthesize_all_node_pairs()

if __name__ == "__main__":
    main()

