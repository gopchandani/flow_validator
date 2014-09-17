__author__ = 'Rakesh Kumar'

import json

import networkx as nx
from networkx.readwrite import json_graph

from model.model import Model


model = Model()
graph = model.get_node_graph()
host_ids = model.get_host_ids()
switch_ids = model.get_switch_ids()

print "Hosts in the graph:", host_ids
print "Switches in the graph:", switch_ids

# Print out graph info as a sanity check
print "Number of nodes add in the graph:", graph.number_of_nodes()

print "Topological paths from 10.0.0.1 -> 10.0.0.4"
asp = nx.all_simple_paths(graph, source="10.0.0.1", target="10.0.0.4")
for p in asp:
    print p

# write json formatted data to use in visualization
d = json_graph.node_link_data(graph)
json.dump(d, open('topo.json', 'w'))
print('Wrote node-link JSON data')
