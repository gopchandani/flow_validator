__author__ = 'Rakesh Kumar'


import networkx as nx
import sys

from model.model import Model
from model.match import Match
from netaddr import IPNetwork

class PortMap:

    def __init__(self, model):
        self.model = model

    def perform_wildcard_analysis(self):
        pass

    #TODO: Methods for events


def main():

    m = Model()
    pm = PortMap(m)
    pm.perform_wildcard_analysis()
    pm.add_switch()

if __name__ == "__main__":
    main()
