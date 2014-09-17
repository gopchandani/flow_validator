__author__ = 'Rakesh Kumar'

import networkx as nx

from model.model import Model


class BackupPaths:
    def __init__(self):
        self.model = Model()
        self.graph = self.model.get_node_graph()
        self.host_ids = self.model.get_host_ids()
        self.switch_ids = self.model.get_switch_ids()

    def analyze_all_node_pairs(self):

        print "Hosts in the graph:", self.host_ids
        print "Switches in the graph:", self.switch_ids
        print "Number of nodes add in the graph:", self.graph.number_of_nodes()

        print "Checking for backup paths between all possible host pairs..."
        for src_host_id in self.host_ids:
            for dst_host_id in self.host_ids:
                print 'Path from', src_host_id, 'to', dst_host_id

                print "Topological paths:"
                asp = nx.all_simple_paths(self.graph, source=src_host_id, target=dst_host_id)
                for p in asp:
                    print p

                    for node in p:
                        print "node id", node, "graph node", self.graph.node[node]


def main():
    bp = BackupPaths()
    bp.analyze_all_node_pairs()


if __name__ == "__main__":
    main()
