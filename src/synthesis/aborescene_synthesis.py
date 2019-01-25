__author__ = 'Rakesh Kumar'

import networkx as nx
import sys
import json

from collections import defaultdict
from copy import deepcopy
from model.intent import Intent


class AboresceneSynthesis(object):

    def __init__(self, params):

        self.network_graph = None
        self.network_configuration = None
        self.synthesis_lib = None
        self.params = params

        self.dst_k_eda = None
        self.k_eda = dict()

        # VLAN tag constitutes 12 bits.
        # We use 2 left most bits for representing the tree_id
        # And the 10 right most bits for representing the destination switch's id
        self.num_bits_for_k = 2
        self.num_bits_for_switches = 10

        self.apply_group_intents_immediately = params["apply_group_intents_immediately"]

        self.sw_intent_lists = defaultdict(defaultdict)

        # As a packet arrives, these are the tables it is evaluated against, in this order:

        # If the packet belongs to a local host, just pop any tags and send it along.
        self.local_mac_forwarding_rules = 0

        # Rules for taking packets arriving from other switches with vlan tags.
        self.other_switch_vlan_tagged_packet_rules = 1

        # If the packet belongs to some other switch, compute the vlan tag based on the destination switch
        # and the tree that would be used and send it along to next table
        self.tree_vlan_tag_push_rules = 2

        # Use the vlan tag as a match and forward using appropriate tree
        self.aborescene_forwarding_rules = 3

    def __str__(self):
        params_str = ''
        for k, v in self.params.items():
            if k == "dst_k_eda_path":
                continue
            params_str += "_" + str(k) + "_" + str(v)
        return self.__class__.__name__ + params_str

    # Gets a switch-only multi-di-graph for the present topology
    def get_mdg(self):

        mdg = nx.MultiDiGraph()

        for n1 in self.network_graph.graph:

            # Don't add any edges for host links
            if self.network_graph.get_node_type(n1) == "host":
                continue

            neigs = []
            for n2 in self.network_graph.graph.neighbors(n1):
                # Don't add any edges for host links
                if self.network_graph.get_node_type(n2) == "host":
                    continue

                neigs.append(n2)

            for i, n2 in enumerate(neigs):
                mdg.add_edge(n1, n2, weight=10000)

        return mdg

    def compute_shortest_path_tree(self, dst_sw):

        spt = nx.DiGraph()

        mdg = self.get_mdg()

        paths = nx.shortest_path(mdg, source=dst_sw.node_id)

        for src in paths:

            if src == dst_sw.node_id:
                continue

            for i in range(len(paths[src]) - 1):
                spt.add_edge(paths[src][i], paths[src][i+1])

        return spt

    def compute_k_edge_disjoint_aborescenes(self, dst_sw):

        k_eda = []

        mdg = self.get_mdg()

        dst_sw_preds = sorted(list(mdg.predecessors(dst_sw.node_id)))
        dst_sw_succs = sorted(list(mdg.successors(dst_sw.node_id)))

        # Remove the predecessor edges to dst_sw, to make it the "root"
        for pred in dst_sw_preds:
            mdg.remove_edge(pred, dst_sw.node_id)

        # Initially, remove all successors edges of dst_sw as well
        for succ in dst_sw_succs:
            mdg.remove_edge(dst_sw.node_id, succ)

        for i in range(self.params["k"]):

            # Assume there are always k edges as the successor of the dst_sw
            for j in range(self.params["k"]):
                if i == j:
                    mdg.add_edge(dst_sw.node_id, dst_sw_succs[j], weight=1)
                else:
                    if mdg.has_edge(dst_sw.node_id, dst_sw_succs[j]):
                        mdg.remove_edge(dst_sw.node_id, dst_sw_succs[j])

            # Compute and store one
            msa = nx.minimum_spanning_arborescence(mdg)
            k_eda.append(msa)

            # If there are predecessors of dst_sw now, we could not find k msa, so break
            if len(list(msa.predecessors(dst_sw.node_id))) > 0:
                print "Could not find k msa."
                break

            # Remove its arcs from mdg to ensure that these arcs are not part of any future msa
            for arc in msa.edges():
                mdg.remove_edge(arc[0], arc[1])

                if arc[0] != dst_sw.node_id and arc[1] != dst_sw.node_id:
                    if mdg.has_edge(arc[1], arc[0]):
                        prev_weight = mdg[arc[1]][arc[0]][0]['weight']
                        mdg.remove_edge(arc[1], arc[0])
                        mdg.add_edge(arc[1], arc[0], weight=prev_weight+100)

        return k_eda

    def compute_sw_intent_lists(self, dst_sw, flow_match, tree, tree_id):
        for src_n in tree:
            src_sw = self.network_graph.get_node_object(src_n)
            for pred in tree.predecessors(src_n):
                link_port_dict = self.network_graph.get_link_ports_dict(src_n, pred)
                out_port = link_port_dict[src_n]

                intent = Intent("primary", flow_match, "all", out_port)
                intent.tree_id = tree_id
                intent.tree = tree

                if src_sw in self.sw_intent_lists:
                    if dst_sw in self.sw_intent_lists[src_sw]:
                        self.sw_intent_lists[src_sw][dst_sw].append(intent)
                    else:
                        self.sw_intent_lists[src_sw][dst_sw] = [intent]
                else:
                    self.sw_intent_lists[src_sw][dst_sw] = [intent]

    def install_group_flow_pair(self, sw, flow_match, sw_intent_list, modified_tags, priority):
        group_id = self.synthesis_lib.push_fast_failover_group_set_vlan_action(sw.node_id,
                                                                               sw_intent_list,
                                                                               modified_tags)

        flow = self.synthesis_lib.push_match_per_in_port_destination_instruct_group_flow(
            sw.node_id,
            self.aborescene_forwarding_rules,
            group_id,
            priority,
            flow_match,
            self.apply_group_intents_immediately)

    def install_failover_group_vlan_tag_flow(self, src_sw, dst_sw):

        # Tags: as they are applied to packets leaving on a given tree in the failover buckets.
        modified_tags = []
        for i in range(self.params["k"]):
            modified_tags.append(int(dst_sw.synthesis_tag) | (i + 1 << self.num_bits_for_switches))

        # Failover rules/group for different match for every single tree
        for i in range(self.params["k"]-1):
            sw_intent_list = deepcopy(self.sw_intent_lists[src_sw][dst_sw])

            # Push a group/vlan_id setting flow rule
            flow_match = deepcopy(sw_intent_list[0].flow_match)
            flow_match["vlan_id"] = int(dst_sw.synthesis_tag) | (i + 1 << self.num_bits_for_switches)

            self.install_group_flow_pair(src_sw, flow_match, sw_intent_list[i:], modified_tags[i:], 1)

    def bolt_back_failover_group_vlan_tag_flow(self, src_sw, dst_sw):

        # Tags: as they are applied to packets leaving on a given tree in the failover buckets.
        modified_tags = []
        for i in range(self.params["k"]):
            modified_tags.append(int(dst_sw.synthesis_tag) | (i + 1 << self.num_bits_for_switches))

        for adjacent_sw_id, link_data in self.network_graph.get_adjacent_switch_link_data(src_sw.node_id):

            for i in range(len(self.sw_intent_lists[src_sw][dst_sw])):
                sw_intent_list = deepcopy(self.sw_intent_lists[src_sw][dst_sw])

                # If the intent is such that it is sending the packet back out to the adjacent switch...
                if sw_intent_list[i].out_port == link_data.link_ports_dict[src_sw.node_id]:

                    # Find the original intent from the adj_sw-> src_sw
                    # This is equivalent to finding the tree with that arc on a lower eda
                    for j in xrange(0, i):
                        eda = self.k_eda[dst_sw.node_id][j]
                        if eda.has_edge(src_sw.node_id, adjacent_sw_id):

                            # Set the in_port here, this gets read by synthesis_lib!
                            sw_intent_list[i].in_port = link_data.link_ports_dict[src_sw.node_id]

                            flow_match = deepcopy(sw_intent_list[i].flow_match)
                            flow_match["in_port"] = link_data.link_ports_dict[src_sw.node_id]

                            # The match is on the base VLAN because this flow just has an IN_PORT replacement
                            flow_match["vlan_id"] = modified_tags[0]

                            self.install_group_flow_pair(src_sw, flow_match,
                                                         sw_intent_list,
                                                         modified_tags,
                                                         2)

                            # This is assuming that each intent only has a single bolt-back counterpart
                            break

    def install_all_group_vlan_tag_flow(self, src_sw, dst_sw):

        # Tags: as they are applied to packets leaving on a given tree in the failover buckets.
        modified_tag = int(dst_sw.synthesis_tag) | ((self.params["k"]) << self.num_bits_for_switches)
        sw_intent_list = [self.sw_intent_lists[src_sw][dst_sw][self.params["k"]-1]]

        flow_match = deepcopy(sw_intent_list[0].flow_match)
        flow_match["vlan_id"] = int(dst_sw.synthesis_tag) | ((self.params["k"]) << self.num_bits_for_switches)

        group_id = self.synthesis_lib.push_select_all_group_set_vlan_action(src_sw.node_id,
                                                                            sw_intent_list,
                                                                            modified_tag)

        flow = self.synthesis_lib.push_match_per_in_port_destination_instruct_group_flow(
            src_sw.node_id,
            self.aborescene_forwarding_rules,
            group_id,
            1,
            flow_match,
            self.apply_group_intents_immediately)

    def push_sw_intent_lists(self, flow_match):

        for src_sw in self.sw_intent_lists:
            print "-- Pushing at Switch:", src_sw.node_id
            for dst_sw in self.sw_intent_lists[src_sw]:

                # Install the rules to put the vlan tags on for hosts that are at this destination switch
                self.push_src_sw_vlan_push_intents(src_sw, dst_sw, flow_match)

                # Install flow rules for 1st ... k - 1 aborescene
                self.install_failover_group_vlan_tag_flow(src_sw, dst_sw)

                # Install the flow rules for the bolt-back case on 1st -- k -1 aborescene
                self.bolt_back_failover_group_vlan_tag_flow(src_sw, dst_sw)

                # Install the flow rules for the kth aborescene...
                self.install_all_group_vlan_tag_flow(src_sw, dst_sw)

    def push_src_sw_vlan_push_intents(self, src_sw, dst_sw, flow_match):
        for h_obj in dst_sw.attached_hosts:
            host_flow_match = deepcopy(flow_match)
            mac_int = int(h_obj.mac_addr.replace(":", ""), 16)
            host_flow_match["ethernet_destination"] = int(mac_int)
            host_flow_match["vlan_id"] = sys.maxsize
            host_flow_match["in_port"] = sys.maxsize

            push_vlan_tag_intent = Intent("push_vlan", host_flow_match, "all", "all")

            push_vlan_tag_intent.required_vlan_id = int(dst_sw.synthesis_tag) | (1 << self.num_bits_for_switches)

            self.synthesis_lib.push_vlan_push_intents(src_sw.node_id,
                                                      [push_vlan_tag_intent],
                                                      self.tree_vlan_tag_push_rules)

    def push_local_mac_forwarding_rules_rules(self, sw, flow_match):

        for h_obj in sw.attached_hosts:
            host_flow_match = deepcopy(flow_match)
            mac_int = int(h_obj.mac_addr.replace(":", ""), 16)
            host_flow_match["ethernet_destination"] = int(mac_int)

            edge_ports_dict = self.network_graph.get_link_ports_dict(h_obj.sw.node_id, h_obj.node_id)
            out_port = edge_ports_dict[h_obj.sw.node_id]
            host_mac_intent = Intent("mac", host_flow_match, "all", out_port)

            self.synthesis_lib.push_destination_host_mac_intents(sw.node_id,
                                                                 [host_mac_intent],
                                                                 self.local_mac_forwarding_rules)

    def push_other_switch_vlan_tagged_packet_rules(self, sw, flow_match):

        table_jump_flow_match = deepcopy(flow_match)

        self.synthesis_lib.push_vlan_tagged_table_jump_rule(sw.node_id,
                                                            flow_match,
                                                            self.other_switch_vlan_tagged_packet_rules,
                                                            self.aborescene_forwarding_rules)

    def record_host_host_primary_paths(self, src_sw_node_id, dst_sw_node_id, p, failed_edge=None):

        src_sw = self.network_graph.get_node_object(src_sw_node_id)
        dst_sw = self.network_graph.get_node_object(dst_sw_node_id)

        for src_host in src_sw.attached_hosts:
            for dst_host in dst_sw.attached_hosts:

                switch_port_tuple_list = []
                in_port = src_host.switch_port.port_number

                for i in xrange(len(p) - 1):
                    edge_ports_dict = self.network_graph.get_link_ports_dict(p[i], p[i + 1])
                    out_port = edge_ports_dict[p[i]]
                    switch_port_tuple_list.append((p[i], in_port, out_port))
                    in_port = edge_ports_dict[p[i + 1]]

                switch_port_tuple_list.append((p[len(p) - 1], in_port, dst_host.switch_port.port_number))

                if not failed_edge:
                    self.synthesis_lib.record_primary_path(src_host, dst_host, switch_port_tuple_list)
                else:
                    self.synthesis_lib.record_failover_path(src_host, dst_host, failed_edge, switch_port_tuple_list)

    def record_paths(self, dst_sw, k_eda):

        # First the primary paths
        primary_tree = k_eda[0]
        failover_tree = k_eda[1]

        sw_primary_tree_paths = defaultdict(defaultdict)
        sw_failover_tree_paths = defaultdict(defaultdict)

        for src_n in primary_tree:

            if dst_sw.node_id == src_n:
                continue

            # Guaranteed to have a path like from each source to the destination in the Arborescence
            path = list(nx.all_simple_paths(primary_tree, dst_sw.node_id, src_n))[0]
            path.reverse()

            sw_primary_tree_paths[src_n][dst_sw.node_id] = path
            self.record_host_host_primary_paths(src_n, dst_sw.node_id, path)

        for src_n in failover_tree:

            if dst_sw.node_id == src_n:
                continue

            # Guaranteed to have a path like from each source to the destination in the Arborescence
            path = list(nx.all_simple_paths(failover_tree, dst_sw.node_id, src_n))[0]
            path.reverse()

            sw_failover_tree_paths[src_n][dst_sw.node_id] = path

        for src_sw_node in sw_primary_tree_paths:
            for dst_sw_node in sw_primary_tree_paths[src_sw_node]:
                primary_path = sw_primary_tree_paths[src_sw_node][dst_sw_node]
                for i in range(len(primary_path) - 1):
                    e = primary_path[i], primary_path[i + 1]

                    primary_path_chunk = primary_path[0:i]
                    failover_path = sw_failover_tree_paths[primary_path[i]][dst_sw_node]
                    total_path = primary_path_chunk + failover_path
                    self.record_host_host_primary_paths(src_sw_node, dst_sw_node, total_path, e)

        self.synthesis_lib.save_synthesized_paths(self.network_configuration.conf_path)

    def synthesize_all_switches(self, flow_match):

        if "dst_k_eda_path" in self.params:
            with open(self.params["dst_k_eda_path"], "r") as infile:
                self.dst_k_eda = dict()
                read_dst_k_eda = json.loads(infile.read())

                for dst_sw_node in read_dst_k_eda:
                    self.dst_k_eda[dst_sw_node] = []
                    for edge_list in read_dst_k_eda[dst_sw_node]:
                        self.dst_k_eda[dst_sw_node].append([tuple(l) for l in edge_list])

        else:
            self.dst_k_eda = dict()
            # For each possible switch that can be a destination for traffic
            for dst_sw in self.network_graph.get_switches():
                if dst_sw.attached_hosts:
                    k_eda = self.compute_k_edge_disjoint_aborescenes(dst_sw)
                    self.dst_k_eda[dst_sw.node_id] = [list(x.edges()) for x in k_eda]

            with open(self.network_configuration.conf_path + "/dst_k_eda.json", "w") as outfile:
                json.dump(self.dst_k_eda, outfile, indent=4)

        # For each possible switch that can be a destination for traffic
        for dst_sw in self.network_graph.get_switches():

            # Push table switch rules
            self.synthesis_lib.push_table_miss_goto_next_table_flow(dst_sw.node_id,
                                                                    self.local_mac_forwarding_rules)
            self.synthesis_lib.push_table_miss_goto_next_table_flow(dst_sw.node_id,
                                                                    self.other_switch_vlan_tagged_packet_rules)
            self.synthesis_lib.push_table_miss_goto_next_table_flow(dst_sw.node_id,
                                                                    self.tree_vlan_tag_push_rules)

            self.push_other_switch_vlan_tagged_packet_rules(dst_sw, flow_match)

            if dst_sw.attached_hosts:

                self.push_local_mac_forwarding_rules_rules(dst_sw, flow_match)

                k_eda = []
                for edges in self.dst_k_eda[dst_sw.node_id]:
                    k_eda.append(nx.MultiDiGraph(edges))

                self.k_eda[dst_sw.node_id] = k_eda

                self.record_paths(dst_sw, k_eda)

                for i in range(self.params["k"]):
                    self.compute_sw_intent_lists(dst_sw, flow_match, k_eda[i], i+1)

        self.push_sw_intent_lists(flow_match)
