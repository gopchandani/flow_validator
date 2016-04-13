__author__ = 'Rakesh Kumar'

import networkx as nx

from collections import defaultdict
from synthesis.synthesis_lib import SynthesisLib
from model.intent import Intent
from model.match import Match

class SynthesizeFailoverAborescene():

    def __init__(self, network_graph):

        self.network_graph = network_graph
        self.synthesis_lib = SynthesisLib("localhost", "8181", self.network_graph)

        self.apply_tag_intents_immediately = True
        self.apply_other_intents_immediately = True

        # per src switch, per dst switch, intents
        self.sw_intents = defaultdict(defaultdict)

    def push_dst_sw_host_intent(self, sw, h_obj, flow_match):

        edge_ports_dict = self.network_graph.get_link_ports_dict(h_obj.switch_id, h_obj.node_id)
        out_port = edge_ports_dict[h_obj.switch_id]
        host_mac_intent = Intent("mac", flow_match, "all", out_port)

        self.synthesis_lib.push_destination_host_mac_intent_flow(sw,
                                                                 host_mac_intent,
                                                                 0,
                                                                 12)


    def compute_intents(self, dst_h_obj, flow_match):

        self.push_dst_sw_host_intent(dst_h_obj.switch_id, dst_h_obj, flow_match)

        nmdg = nx.MultiDiGraph(self.network_graph.graph)

        for n in self.network_graph.graph:
            node_type = self.network_graph.get_node_type(n)
            node_obj = self.network_graph.get_node_object(n)

            # Remove all host nodes
            if node_type == "host":
                nmdg.remove_node(n)

            # Set the weights of ingress edges to destination switch to less than 1
            if node_type == "host" and dst_h_obj.node_id == node_obj.node_id:
                for pred in nmdg.predecessors(node_obj.switch_id):
                    nmdg[pred][node_obj.switch_id][0]['weight'] = 0.5

        msa = nx.maximum_spanning_arborescence(nmdg)

        # Go through each node of the msa and check its successors
        for n in msa:
            for pred in msa.predecessors(n):

                link_port_dict = self.network_graph.get_link_ports_dict(n, pred)
                out_port = link_port_dict[n]

                self.sw_intents[n][dst_h_obj.switch_id] = Intent("primary",
                                                                 flow_match,
                                                                 "all",
                                                                 out_port)

    def push_intents(self):

        for src_sw in self.sw_intents:

            print "-- Pushing at Switch:", src_sw

            for dst_sw in self.sw_intents[src_sw]:

                group_id = self.synthesis_lib.push_select_all_group(src_sw, [self.sw_intents[src_sw][dst_sw]])

                flow = self.synthesis_lib.push_match_per_in_port_destination_instruct_group_flow(
                        src_sw,
                        0,
                        group_id,
                        1,
                        self.sw_intents[src_sw][dst_sw].flow_match,
                        self.sw_intents[src_sw][dst_sw].apply_immediately)

    def synthesize_all_dsts(self):

        print "Synthesizing backup paths between all possible host pairs..."

        for dst in self.network_graph.host_ids:

            dst_h_obj = self.network_graph.get_node_object(dst)

            print "-----------------------------------------------------------------------------------------------"
            print 'Synthesizing paths to', dst
            print "-----------------------------------------------------------------------------------------------"

            flow_match = Match(is_wildcard=True)
            flow_match["ethernet_type"] = 0x0800
            mac_int = int(dst_h_obj.mac_addr.replace(":", ""), 16)
            flow_match["ethernet_destination"] = int(mac_int)

            self.compute_intents(dst_h_obj, flow_match)
            print "-----------------------------------------------------------------------------------------------"

        self.push_intents()
