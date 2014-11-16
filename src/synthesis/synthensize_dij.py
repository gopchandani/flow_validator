
__author__ = 'Rakesh Kumar'

from model.model import Model
from model.match import Match

from synthesis.synthesis_lib import SynthesisLib
from synthesis.intent import Intent

from collections import defaultdict


import pprint
import networkx as nx

class SynthesizeDij():

    def __init__(self):

        self.model = Model()
        self.synthesis_lib = SynthesisLib("localhost", "8181", self.model)

        # s represents the set of all switches that are
        # affected as a result of flow synthesis
        self.s = set()

    def get_forwarding_intents_dict(self, sw):

        forwarding_intents = None

        if "forwarding_intents" in self.model.graph.node[sw]:
            forwarding_intents = self.model.graph.node[sw]["forwarding_intents"]
        else:
            forwarding_intents = dict()
            self.model.graph.node[sw]["forwarding_intents"] = forwarding_intents

        return forwarding_intents

    def _compute_path_forwarding_intents(self, p, intent_type, flow_match, switch_in_port=None):

        src_node = p[0]
        dst = p[len(p) -1]

        edge_ports_dict = None
        out_port = None
        in_port = None

        # Sanity check -- Check that last node of the p is a host, no matter what
        if self.model.graph.node[p[len(p) - 1]]["node_type"] != "host":
            raise Exception("The last node in the p has to be a host.")

        # Check whether the first node of path is a host or a switch.
        if self.model.graph.node[p[0]]["node_type"] == "host":

            #Traffic arrives from the host to first switch at switch's port
            edge_ports_dict = self.model.get_edge_port_dict(p[0], p[1])
            in_port = edge_ports_dict[p[1]]

            # Traffic leaves from the first switch's port
            edge_ports_dict = self.model.get_edge_port_dict(p[1], p[2])
            out_port = edge_ports_dict[p[1]]

            p = p[1:]

        elif self.model.graph.node[p[0]]["node_type"] == "switch":
            if not switch_in_port:
                raise Exception("switching_in_port needed.")

            in_port = switch_in_port
            edge_ports_dict = self.model.get_edge_port_dict(p[0], p[1])
            out_port = edge_ports_dict[p[0]]

        # This look always starts at a switch
        for i in range(len(p) - 1):

            #  Add the switch to set S
            self.s.add(p[i])

            #  Add the intent to the switch's node in the graph
            forwarding_intents = self.get_forwarding_intents_dict(p[i])
            forwarding_intent = Intent(intent_type, flow_match, in_port, out_port)

            if dst in forwarding_intents:
                forwarding_intents[dst][forwarding_intent] += 1
            else:
                forwarding_intents[dst] = defaultdict(int)
                forwarding_intents[dst][forwarding_intent] = 1

            # Prepare for next switch along the path if there is a next switch along the path
            if self.model.graph.node[p[i+1]]["node_type"] != "host":

                # Traffic arrives from the host to first switch at switch's port
                edge_ports_dict = self.model.get_edge_port_dict(p[i], p[i+1])
                in_port = edge_ports_dict[p[i+1]]

                # Traffic leaves from the first switch's port
                edge_ports_dict = self.model.get_edge_port_dict(p[i+1], p[i+2])
                out_port = edge_ports_dict[p[i+1]]

    def dump_forwarding_intents(self):
        for sw in self.s:

            print "---", sw, "---"

            for port in self.model.graph.node[sw]["sw"].ports:
                print self.model.graph.node[sw]["sw"].ports[port]

            pprint.pprint(self.model.graph.node[sw]["forwarding_intents"])

    def _get_intents(self, dst_intents, intent_type):

        return_intent = []

        for intent in dst_intents:
            if intent.intent_type == intent_type:
                return_intent.append(intent)

        return return_intent

    def _identify_reverse_and_balking_intents(self):

        for sw in self.s:
            for dst in self.model.graph.node[sw]["forwarding_intents"]:
                dst_intents = self.model.graph.node[sw]["forwarding_intents"][dst]

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

    def synthesize_flow(self, src_host, dst_host, flow_match):

        #  First find the shortest path between src and dst.
        p = nx.shortest_path(self.model.graph, source=src_host, target=dst_host)
        print "Primary Path:", p

        #  Compute all forwarding intents as a result of primary path
        self._compute_path_forwarding_intents(p, "primary", flow_match)

        #  Along the shortest path, break a link one-by-one
        #  and accumulate desired action buckets in the resulting path
        edge_ports_dict = self.model.get_edge_port_dict(p[0], p[1])

        in_port = edge_ports_dict[p[1]]

        #  Go through the path, one edge at a time
        for i in range(1, len(p) - 2):

            # Keep a copy of this handy
            edge_ports_dict = self.model.get_edge_port_dict(p[i], p[i+1])

            # Delete the edge
            self.model.graph.remove_edge(p[i], p[i + 1])

            # Find the shortest path that results when the link breaks
            # and compute forwarding intents for that
            bp = nx.shortest_path(self.model.graph, source=p[i], target=dst_host)
            print "Backup Path", bp

            self._compute_path_forwarding_intents(bp, "failover", flow_match, in_port)

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

                self.synthesize_flow(src, dst, flow_match)

                print "--------------------------------------------------------------------------------------------------------"


        self._identify_reverse_and_balking_intents()
        self.push_switch_changes()

def main():
    sm = SynthesizeDij()
    sm.synthesize_all_node_pairs()

if __name__ == "__main__":
    main()

