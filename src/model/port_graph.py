__author__ = 'Rakesh Kumar'

import networkx as nx
from collections import deque

import sys

from netaddr import IPNetwork
from copy import deepcopy

from port import Port
from match import Match, MatchElement

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

    def get_table_port(self, switch_id, table_number):
        return self.g.node[self._get_table_port_id(switch_id,table_number)]["p"]

    def add_port(self, port):
        self.g.add_node(port.port_id, p=port)

    def remove_port(self):
        pass

    def get_port(self, port_id):
        return self.g.node[port_id]["p"]

    def add_edge(self, port1, port2, matching_element, is_active=True, modified_fields={}):


        # There are two types of edges, ones that trigger applications of all written rules thus far
        # and ones that don't. Only edges that are between two switches, trigger application of written actions
        # Because that's when a packet leaves a switch (OF1.3 specification's time of applying rules)
        #TODO:

        edge_data = {"matching_element": matching_element,
                     "is_active": is_active,
                     "modified_fields": modified_fields}

        e = (port1.port_id, port2.port_id)

        print e, modified_fields

        self.g.add_edge(*e, edge_data=edge_data)

    def remove_edge(self, port1, port2):
        pass
        # Look at the source port and see what admitted_matches rely on this edge to be admitted
        # TODO: Store that information in the first place

        # Ones that do, need to be found alternatives... This can be achieved by looking at other outgoing edges
        # that may be active now...

        # If the admitted matches chance (i,e. their content changes), everybody who relies on that edge needs to be
        # updated, so the change travels back in the bfs fashion

    def get_edge_data(self, node1, node2):
        a = self.g[node1][node2]
        return a[0]['edge_data']

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
                port1 = self.get_port(node_edge[0] + ":" + edge_port_dict[node_edge[0]])
                port2 = self.get_port(node_edge[1] + ":" + edge_port_dict[node_edge[1]])

                self.add_edge(port1, port2, MatchElement(is_wildcard=True))
                self.add_edge(port2, port1, MatchElement(is_wildcard=True))

    def update_edge_down(self):
        pass

    def update_edge_up(self):
        pass

    def add_destination_host_port_traffic(self, host_obj, admitted_match):

        # Add the port for host
        hp = Port(None, port_type="physical", port_id=host_obj.node_id)
        hp.admitted_match[host_obj.node_id] = admitted_match
        self.add_port(hp)

        # Add edges between host and switch in the port graph
        self.add_edge(hp, host_obj.switch_port, MatchElement(is_wildcard=True))
        self.add_edge(host_obj.switch_port, hp, MatchElement(is_wildcard=True))

        return hp

    def remove_destination_host(self, host_obj):
        pass

    def bfs_active_edges(self, G, source, reverse=False):

        if reverse and isinstance(G, nx.DiGraph):
            neighbors = G.predecessors_iter
        else:
            neighbors = G.neighbors_iter

        visited = set([source])
        queue = deque([(source, neighbors(source))])
        edge_data = None

        while queue:
            parent, children = queue[0]
            try:
                child = next(children)

                if reverse:
                    edge_data = self.get_edge_data(child, parent)
                else:
                    edge_data = self.get_edge_data(parent, child)

                if child not in visited and edge_data["is_active"]:

                    if reverse:
                        yield self.get_port(parent), self.get_port(child), edge_data
                    else:
                        yield self.get_port(child), self.get_port(parent), edge_data

                    visited.add(child)
                    queue.append((child, neighbors(child)))

            except StopIteration:
                queue.popleft()


    def compute_destination_edges(self, dst):


        # Traverse in reverse.
        for next_port, curr_port, edge_data in self.bfs_active_edges(self.g, dst, reverse=True):

            print curr_port.port_id, "->", next_port.port_id

            # At curr_port, set up the admitted traffic for the destination_port, by examining
            # admitted_matches at next_port
            if dst in next_port.admitted_match:

                if edge_data["modified_fields"] and edge_data["matching_element"]:
                    transformed_match = next_port.admitted_match[dst]
                    original_match = transformed_match.get_orig_match(edge_data["modified_fields"].keys(),
                                                                      edge_data["matching_element"])
                    curr_port.admitted_match[dst] = original_match

                elif edge_data["matching_element"]:
                    # TODO: This should really be passed down as part of the "flow"
                    m = Match()
                    m.match_elements.append(edge_data["matching_element"])

                    if not next_port.admitted_match[dst].intersect(m).is_empty():
                        curr_port.admitted_match[dst] = next_port.admitted_match[dst]
                else:
                    pass