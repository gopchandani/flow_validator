__author__ = 'Rakesh Kumar'

import networkx as nx
import sys

from netaddr import IPNetwork
from copy import deepcopy

from port import Port
from match import Match

class PortGraph:

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

    def add_edge(self, port1, port2, match, actions):

        edge_data = {"match": match, "actions": actions}
        e = (port1.port_id, port2.port_id)
        self.g.add_edge(*e, edge_data=edge_data)

    def remove_edge(self):
        pass

    def get_edge_data(self, node1, node2):
        return self.g[node1.node_id][node2.node_id]['edge_data']

    def init_port_graph(self):

        # Iterate through switches and add the ports and relevant abstract analysis
        for sw in self.model.get_switches():
            sw.compute_switch_port_graph()

        #TODO: Do something for ports between the switches, representing physical topology

    def update_edge_down(self):
        pass

    def update_edge_up(self):
        pass

    # This function populates the port graph with edges and match state
    def populate_port_graph(self, port):

        # Before this function gets triggered for a specific destination host, we need some
        # abstract, generic analysis prepared that applies to more than this host. This pre-analysis need to consider
        # how a wildcard flow moves from one port to another in the switch through all the tables.

        # What I just described above is essentially what a transfer function does right now. If we keep that inside it,
        # Then the transfer function essentially needs to be pre-computed once and then queried by ports as hosts for analysis
        # get added

        # Capture the action_list for ports before and after a table for a wildcard match,
        # The path from one external facing port to another goes through a sequence of action lists
        # This breaks when the next action depends on changes that have already been made to the header
        # aka apply-action
        # The same nature of things also applies when we are traversing switch boundaries, except the action_list
        # is empty
        # Each switch port has entries for all the destination switches +
        # hosts that are directly to the switch as destinations

        # for destination in port.destination_match:
        #
        #     destination_match = deepcopy(port.destination_match[destination])
        #
        #     destination_match.in_port = "all"
        #     for i in range(len(port.sw.flow_tables)):
        #
        #         table_port = self._get_table_port(port.sw.node_id, i)
        #         print table_port.port_id
        #         print port.sw.flow_tables[i].table_id
        #
        #         hpm_flow, intersection = port.sw.flow_tables[i].get_highest_priority_matching_flow(destination_match)
        #
        #
        #         #TODO: Need something on the lines of get_hpm_flow_actions_list
        #         print hpm_flow.applied_actions
        #         print hpm_flow.written_actions

        for destination in port.destination_match:

            # See what other ports on this switch can reach this port and with what match
            for sw_port in port.sw.ports.values():

                if sw_port != port:
                    destination_match = deepcopy(port.destination_match[destination])
                    destination_match.in_port = sw_port.port_number
                    output_match = port.sw.transfer_function(destination_match)
                    sw_port.destination_match[destination] = output_match[port.port_number]

        # Takes a destination port, and source port and computes precisely just that.
    
        # Go a level higher, i.e. Go to the ports that are physically 
        # connected to ports in this switch from other switches and then compute the same from there.
        # This sounds _eerily_ recursive. :)

        # These other ports can not be things that we have already seen though

        #This whole thing terminates at ports that are connected to other switches.
        #This sounds eerily like the end case of recursion

    def perform_wildcard_analysis(self):
        for h in self.model.get_hosts():

            # Inject a wild-card (albeit with some realism) at the appropriate port
            # This here specifies the

            in_port_match = Match(tag="match@" + str(h.node_id), init_wildcard=True)
            in_port_match.set_field("ethernet_type", 0x0800)
            src_mac_int = int(h.mac_addr.replace(":", ""), 16)
            in_port_match.set_field("ethernet_source", src_mac_int)
            in_port_match.set_field("has_vlan_tag", 0)

            h.switch_port.destination_match[h.mac_addr] = in_port_match

            self.populate_port_graph(h.switch_port)

            break

    #TODO: Methods for events
