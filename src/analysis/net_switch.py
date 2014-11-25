__author__ = 'Rakesh Kumar'


import networkx as nx
import sys

from model.model import Model
from model.match import Match
from netaddr import IPNetwork

class NetSwitch:

    def __init__(self, model):
        self.model = model
        self.port_graph = self.init_port_graph()

    def init_port_graph(self):
        port_graph = nx.Graph()

        # Iterate through switches and add the ports
        for sw in self.model.get_switches():
            print sw

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
