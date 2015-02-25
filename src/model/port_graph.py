__author__ = 'Rakesh Kumar'

import networkx as nx
from collections import deque

import sys

from netaddr import IPNetwork
from copy import deepcopy

from port import Port
from match import Match
from flow_path import FlowPathElement


class PortGraph:
    '''

    This function populates the port graph with edges and match state
    Before this function gets triggered for a specific destination host, we need some
    abstract, generic analysis prepared that applies to more than this host. This pre-analysis need to consider
    how a wildcard flow moves from one port to another in the switch through all the tables.

    What I just described above is essentially what a transfer function does right now. If we keep that inside it,
    Then the transfer function essentially needs to be pre-computed once and then queried by ports as hosts for analysis
    get added

    Capture the action_list for ports before and after a table for a wildcard match,
    The path from one external facing port to another goes through a sequence of action lists
    This breaks when the next action depends on changes that have already been made to the header
    aka apply-action
    The same nature of things also applies when we are traversing switch boundaries, except the action_list
    is empty
    Each switch port has entries for all the destination switches +
    hosts that are directly to the switch as destinations
    Takes a destination port, and source port and computes precisely just that.

    Go a level higher, i.e. Go to the ports that are physically
    connected to ports in this switch from other switches and then compute the same from there.
    This sounds _eerily_ recursive. :)

    These other ports can not be things that we have already seen though

    This whole thing terminates at ports that are connected to other switches.
    This sounds eerily like the end case of recursion
    '''

    def __init__(self, model):
        self.model = model
        self.g = nx.MultiDiGraph()
        self.added_host_ports = []

    def get_table_port_id(self, switch_id, table_number):
        return switch_id + ":table" + str(table_number)

    def get_incoming_port_id(self, switch_id, port_number):
        return switch_id + ":incoming" + str(port_number)

    def get_outgoing_port_id(self, switch_id, port_number):
        return switch_id + ":outgoing" + str(port_number)

    def add_port(self, port):
        self.g.add_node(port.port_id, p=port)

    def remove_port(self):
        pass

    def get_port(self, port_id):
        return self.g.node[port_id]["p"]

    def add_edge(self, port1, port2, flow_match, modified_fields={}):

        edge_type = None
        if port1.port_type == "table" and port2.port_type == "outgoing":
            edge_type = "egress"
        elif port1.port_type == "incoming" and port2.port_type == "table":
            edge_type = "ingress"
        elif port1.port_type == "physical" and port2.port_type == "table":
            edge_type = "transport"

        e = (port1.port_id, port2.port_id)
        self.g.add_edge(*e, flow_match=flow_match, modified_fields=modified_fields, edge_type=edge_type)

    def remove_edge(self, port1, port2):
        pass
        # Look at the source port and see what admitted_matches rely on this edge to be admitted
        # TODO: Store that information in the first place

        # Ones that do, need to be found alternatives... This can be achieved by looking at other outgoing edges
        # that may be active now...

        # If the admitted matches chance (i,e. their content changes), everybody who relies on that edge needs to be
        # updated, so the change travels back in the bfs fashion

    def init_global_controller_port(self):
        cp = Port(None, port_type="controller", port_id="4294967293")
        self.add_port(cp)

    def remove_node_graph_edge(self, node1, node2):
        pass

    def init_port_graph(self):

        #Add a port for controller
        #TODO: Nothing gets added to this for now.
        self.init_global_controller_port()

        # Iterate through switches and add the ports and relevant abstract analysis
        for sw in self.model.get_switches():
            sw.compute_switch_port_graph()

        # Add edges between ports on node edges, where nodes are only switches.
        for node_edge in self.model.graph.edges():
            if not node_edge[0].startswith("host") and not node_edge[1].startswith("host"):

                edge_port_dict = self.model.get_edge_port_dict(node_edge[0], node_edge[1])

                from_port = self.get_port(self.get_outgoing_port_id(node_edge[0], edge_port_dict[node_edge[0]]))
                to_port = self.get_port(self.get_incoming_port_id(node_edge[1], edge_port_dict[node_edge[1]]))
                self.add_edge(from_port, to_port, Match(init_wildcard=True))

                from_port = self.get_port(self.get_outgoing_port_id(node_edge[1], edge_port_dict[node_edge[1]]))
                to_port = self.get_port(self.get_incoming_port_id(node_edge[0], edge_port_dict[node_edge[0]]))
                self.add_edge(from_port, to_port, Match(init_wildcard=True))

    def update_edge_down(self):
        pass

    def update_edge_up(self):
        pass

    def add_destination_host_port_traffic(self, host_obj, admitted_match):

        # Add the port for host

        hp = Port(None, port_type="physical", port_id=host_obj.node_id)
        hp.path_elements[host_obj.node_id] = FlowPathElement(host_obj.node_id, admitted_match, None)
        hp.admitted_match[host_obj.node_id] = admitted_match

        self.add_port(hp)
        self.added_host_ports.append(hp)

        # Add edges between host and switch in the port graph

        switch_ingress_port = self.get_port(self.get_incoming_port_id(host_obj.switch_id,
                                                                       host_obj.switch_port_attached))
        switch_egress_port = self.get_port(self.get_outgoing_port_id(host_obj.switch_id,
                                                                      host_obj.switch_port_attached))

        self.add_edge(hp, switch_ingress_port, Match(init_wildcard=True))
        self.add_edge(switch_egress_port, hp, Match(init_wildcard=True))

        host_obj.switch_ingress_port = switch_ingress_port
        host_obj.switch_egress_port = switch_egress_port

        return hp

    def remove_destination_host(self, host_obj):
        pass


    def process_edges(self, predecessor_port, current_port, dst_port_id):

        admitted_match = Match()
        edge_data = self.g.get_edge_data(predecessor_port.port_id, current_port.port_id)

        for edge_data_key in edge_data:

            this_edge = edge_data[edge_data_key]

            if dst_port_id in current_port.path_elements:
                admitted_at_current_port = deepcopy(current_port.path_elements[dst_port_id].admitted_match)

                # You enter the switch at "egress" edges. Yes... Eye-roll:
                # At egress edges, set the in_port of the admitted match for destination to wildcard
                if this_edge["edge_type"] == "egress":
                    admitted_at_current_port.set_field("in_port", is_wildcard=True)

                if this_edge["modified_fields"] and this_edge["flow_match"]:

                    # This is what the match would be before passing this match
                    attempted_match = admitted_at_current_port.get_orig_match(this_edge["modified_fields"],
                                                                           this_edge["flow_match"].match_elements[0])
                elif this_edge["flow_match"]:
                    attempted_match = admitted_at_current_port

                i = attempted_match.intersect(this_edge["flow_match"])
                if not i.is_empty():
                    if dst_port_id in predecessor_port.path_elements:
                        predecessor_port.path_elements[dst_port_id].accumulate_admitted_match(i)
                    else:
                        predecessor_port.path_elements[dst_port_id] = FlowPathElement(predecessor_port.port_id, i,
                                                                                      current_port.path_elements[dst_port_id])

                    admitted_match.union(i)


        return admitted_match


    def next_to_pop(self, queue):

        i = 0
        while i < len(queue):

            try_id = queue[i][0]
            try_port = self.get_port(try_id)

            found_same_level_successor = False
            for successor_id in self.g.successors_iter(try_id):
                successor_port = self.get_port(successor_id)
                if successor_port.traversal_distance == try_port.traversal_distance:
                    found_same_level_successor = True
                    break

            # If not, then break here so that this i could be used for expansion of queue
            if not found_same_level_successor:
                break

        # If all of them have successors in the queue, raise it
        if i > 0 and  i == len(queue) - 1:
            raise Exception('Everybody has successors in the queue')

        return i

    # Starts on a port and tries to carry admitted_traffic to left to everywhere it can reach
    # Initially called with same start_port_id and dst_port_id

    def propagate_admitted_traffic(self, start_port_id, dst_port_id):

        start_port = self.get_port(start_port_id)
        start_port.traversal_distance = 0

        processed = set([start_port_id])
        queue = [(start_port_id, self.g.predecessors_iter(start_port_id))]
        while queue:

            #pop_i = self.next_to_pop(queue)
            pop_i = 0
            current, predecessors = queue[pop_i]

            # This port beats the other to the punch
            if current == "openflow:1:outgoing3":
                pass

            try:
                predecessor = next(predecessors)

                current_port = self.get_port(current)
                predecessor_port = self.get_port(predecessor)
                predecessor_port.traversal_distance = current_port.traversal_distance + 1

                if predecessor not in processed:
                    processed.add(predecessor)
                    admitted_match = self.process_edges(predecessor_port, current_port, dst_port_id)

                    # Check if there was actual propagation of traffic, only then visit the next guy's children
                    if not admitted_match.is_empty():
                        queue.append((predecessor, self.g.predecessors_iter(predecessor)))

            except StopIteration:
                queue.pop(pop_i)


    # Answers what will be admitted by this edge for dst
    def process_curr_port_to_successor_admitted_match(self, dst, curr_port, successor, edge_data):

        print curr_port.port_id, successor.port_id

        if dst in successor.admitted_match:
            admitted_at_successor = deepcopy(successor.admitted_match[dst].admitted_match)

            # You enter the switch at "egress" edges. Yes... Eye-roll:
            # At egress edges, set the in_port of the admitted match for destination to wildcard
            if edge_data["edge_type"] == "egress":
                admitted_at_successor.set_field("in_port", is_wildcard=True)

            if edge_data["modified_fields"] and edge_data["flow_match"]:

                # This is what the match would be before passing this match
                original_match = admitted_at_successor.get_orig_match(edge_data["modified_fields"],
                                                                      edge_data["flow_match"].match_elements[0])
            elif edge_data["flow_match"]:
                original_match = admitted_at_successor

            i = original_match.intersect(edge_data["flow_match"])
            if not i.is_empty():
                return i
            else:
                return None
        else:
            None


    # Takes a node, its admitted_match for destination and the destination
    # Recursively sets up admitted match

    def compute_admitted_match(self, curr, curr_admitted_match, dst_port):

        print curr.port_id, dst_port.port_id

        # First you gather the goods
        if dst_port.port_id not in curr.admitted_match:
            curr.admitted_match[dst_port.port_id] = curr_admitted_match
        else:
            curr.admitted_match[dst_port.port_id].union(curr_admitted_match)

        # Base case: Stop at host ports.
        if curr in self.added_host_ports:
            return
        else:
            print list(self.g.predecessors_iter(curr.port_id))

            # Recursively call myself at each of my predecessors in the port graph
            for pred_id in self.g.predecessors_iter(curr.port_id):

                pred = self.get_port(pred_id)
                pred_admitted_match = self.process_edges(pred, curr, dst_port.port_id)

                if not pred_admitted_match.is_empty():
                    self.compute_admitted_match(pred, pred_admitted_match, dst_port)