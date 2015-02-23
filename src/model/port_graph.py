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

        self.add_port(hp)

        # Add edges between host and switch in the port graph

        switch_incoming_port = self.get_port(self.get_incoming_port_id(host_obj.switch_id,
                                                                       host_obj.switch_port_attached))
        switch_outgoing_port = self.get_port(self.get_outgoing_port_id(host_obj.switch_id,
                                                                      host_obj.switch_port_attached))

        self.add_edge(hp, switch_incoming_port, Match(init_wildcard=True))
        self.add_edge(switch_outgoing_port, hp, Match(init_wildcard=True))

        # # Propagate the traffic down to the switch incoming port
        # switch_incoming_port.path_elements[host_obj.node_id] = FlowPathElement(host_obj.switch_port.port_id,
        #                                                                        admitted_match,
        #                                                                        hp.path_elements[host_obj.node_id])
        #

        return hp

    def remove_destination_host(self, host_obj):
        pass

    def process_edge(self, dst, curr_port, next_port, edge_data):

        print curr_port.port_id, next_port.port_id

        # This is another path which is being stopped by pure BFS way of doing this...
        #if curr_port.port_id == "openflow:3:table1" and next_port.port_id == "openflow:3:table2":

        # This is where the loop happens
        if curr_port.port_id == "openflow:1:1" and next_port.port_id == "openflow:1:table0":
            print next_port.path_elements[dst].get_path_str()

        if dst in next_port.path_elements:
            admitted_at_next_port = deepcopy(next_port.path_elements[dst].admitted_match)

            # You enter the switch at "egress" edges. Yes... Eye-roll:
            # At egress edges, set the in_port of the admitted match for destination to wildcard
            if edge_data["edge_type"] == "egress":
                admitted_at_next_port.set_field("in_port", is_wildcard=True)

            if edge_data["modified_fields"] and edge_data["flow_match"]:

                # This is what the match would be before passing this match
                original_match = admitted_at_next_port.get_orig_match(edge_data["modified_fields"],
                                                                      edge_data["flow_match"].match_elements[0])
            elif edge_data["flow_match"]:
                original_match = admitted_at_next_port

            i = original_match.intersect(edge_data["flow_match"])
            if not i.is_empty():
                if dst in curr_port.path_elements:
                    curr_port.path_elements[dst].accumulate_admitted_match(i)
                else:
                    curr_port.path_elements[dst] = FlowPathElement(curr_port.port_id, i, next_port.path_elements[dst])

                return curr_port.path_elements[dst]

    def propagate_admitted_traffic(self, propagation_start_port, dst):

        # A Node is not quite processed, until all of its successors have brought back their
        # admitted match information to it.

        processed = set([dst])

        # start at the port specified
        queue = deque([(propagation_start_port, self.g.predecessors_iter(propagation_start_port))])

        while queue:
            parent, children = queue[0]
            try:
                child = next(children)

                if child not in processed:

                    processed.add(child)

                    explore_children = False
                    edge_data = self.g.get_edge_data(child, parent)
                    for edge_data_key in edge_data:
                        propagated_match = self.process_edge(dst, self.get_port(child),
                                                             self.get_port(parent),
                                                             edge_data[edge_data_key])

                        if propagated_match:
                            explore_children = True

                    # Check if there was actual propagation of traffic, only then visit the next guy's children
                    if explore_children:
                        queue.append((child, self.g.predecessors_iter(child)))

            except StopIteration:
                queue.popleft()