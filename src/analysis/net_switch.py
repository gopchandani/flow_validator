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

    def init_port_graph(self):
        port_graph = nx.Graph()

        # Iterate through switches and add the ports
        for sw in self.model.get_switches():
            for port in sw.ports:
                port_graph.add_node(sw.ports[port])

            if len(sw.flow_tables) > 1:
                for i in range(len(sw.flow_tables) - 1):
                    port_graph.add_node(Port(sw, port_type="table"))

        return port_graph

    def perform_wildcard_analysis(self):
        pass

    #TODO: Methods for events


def main():

    m = Model()
    pm = NetSwitch(m)
    pm.perform_wildcard_analysis()

if __name__ == "__main__":
    main()
