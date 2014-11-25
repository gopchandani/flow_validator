__author__ = 'Rakesh Kumar'


import networkx as nx
import sys

from model.model import Model
from model.match import Match
from netaddr import IPNetwork

class PortMap:

    def __init__(self, model):
        pass

    def add_switch(self):
        pass

    def remove_switch(self):
        pass

    def add_edge(self):
        pass

    def remove_edge(self):
        pass

    def perform_wildcard_analysis(self):
        pass

def main():

    m = Model()
    pm = PortMap(m)
    pm.perform_wildcard_analysis()
    pm.add_switch()

if __name__ == "__main__":
    main()
