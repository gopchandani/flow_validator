__author__ = 'Rakesh Kumar'


import networkx as nx
import sys

from netaddr import IPNetwork

from model.model import Model
from model.port import Port
from model.match import Match


class NetSwitch:

    def __init__(self, model):
        self.model = model
        self.port_graph = self.init_port_graph()

    def _get_table_port_id(self, switch_id, table_number):
        return switch_id + ":table" + str(table_number)

    def _get_table_port(self, switch_id, table_number):
        return self.port_graph.node[self._get_table_port_id(switch_id,table_number)]["p"]

    def init_port_graph(self):
        port_graph = nx.Graph()

        # Iterate through switches and add the ports
        for sw in self.model.get_switches():
            for port in sw.ports:
                port_graph.add_node(sw.ports[port].port_id, p=sw.ports[port])

            for i in range(len(sw.flow_tables)):
                p = Port(sw, port_type="table", port_id=self._get_table_port_id(sw.node_id, i))
                port_graph.add_node(p.port_id, p=p)

        return port_graph

    # This function populates the port graph with edges and match state
    def populate_port_graph(self, starting_port):

        # Capture the action_list for ports before and after a table.
        # The path from one external facing port to another goes through a sequence of action lists
        # This breaks when the next action depends on changes that have already been made to the header
        # aka apply-action

        # See what actions across the tables does this match attract.
        # Some of these actions would be a function of in_port and some won't be. But the match we should try
        # should have in_port set to "all"

        # That is to do this from the prior computation instead of doing transfer function over and it and over again

        # The same nature of things also applies when we are traversing switch boundaries, except the action_list
        # is empty


        input_match = starting_port.host_match
        input_match.in_port = "all"
        for i in range(len(starting_port.sw.flow_tables)):

            table_port = self._get_table_port(starting_port.sw.node_id, i)

            print table_port.port_id
            print starting_port.sw.flow_tables[i].table_id


        # See what other ports on this switch can reach this port and with what match
        for port in starting_port.sw.ports.values():

            if port != starting_port:
                input_match = starting_port.host_match
                input_match.in_port = port.port_number
                output_match = starting_port.sw.transfer_function(input_match)
                port.destination_switch_match[starting_port.port_id] = output_match[starting_port.port_number]


        # TODO: Need to have a method for switch which would do this,
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
            host_match = Match()
            host_match.ethernet_type = 0x0800
            host_match.ethernet_source = h.mac_addr
            host_match.has_vlan_tag = False

            h.switch_port.host_match = host_match

            self.populate_port_graph(h.switch_port)
            break

    #TODO: Methods for events


def main():

    m = Model()
    pm = NetSwitch(m)
    pm.perform_wildcard_analysis()

if __name__ == "__main__":
    main()
