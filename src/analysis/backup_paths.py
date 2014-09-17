__author__ = 'Rakesh Kumar'

import networkx as nx

from model.model import Model


model = Model()
graph = model.get_node_graph()
host_ids = model.get_host_ids()
switch_ids = model.get_switch_ids()

print "Hosts in the graph:", host_ids
print "Switches in the graph:", switch_ids
print "Number of nodes add in the graph:", graph.number_of_nodes()

print "Checking for backup paths between all possible host pairs..."
for src_host_id in host_ids:
    for dst_host_id in host_ids:
        print 'Path from', src_host_id, 'to', dst_host_id

        print "Topological paths:"
        asp = nx.all_simple_paths(graph, source=src_host_id, target=dst_host_id)
        for p in asp:
            print p

            for node in p:
                print "node id", node, "graph node", graph.node[node]
