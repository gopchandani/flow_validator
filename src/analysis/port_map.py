__author__ = 'Rakesh Kumar'


import networkx as nx
import sys

from model.model import Model
from model.match import Match
from netaddr import IPNetwork

class PortMap:

    def __init__(self):
        pass

    def trigger_wildcard_analysis(self):
        pass

def main():
    pm = PortMap()
    pm.perform_wildcard_analysis()

if __name__ == "__main__":
    main()
