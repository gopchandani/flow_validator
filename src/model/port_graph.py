__author__ = 'Rakesh Kumar'

import networkx as nx

class PortGraph(object):

    def __init__(self, network_graph):

        self.network_graph = network_graph
        self.g = nx.DiGraph()

    def get_table_node_id(self, switch_id, table_number):
        return switch_id + ":table" + str(table_number)

    def get_ingress_node_id(self, node_id, port_number):
        return node_id + ":ingress" + str(port_number)

    def get_egress_node_id(self, node_id, port_number):
        return node_id + ":egress" + str(port_number)

    def get_ingress_node(self, node_id, port_number):
        return self.get_node(self.get_ingress_node_id(node_id, port_number))

    def get_egress_node(self, node_id, port_number):
        return self.get_node(self.get_egress_node_id(node_id, port_number))

    def add_node(self, node):
        self.g.add_node(node.node_id, p=node)

    def remove_node(self, node):
        self.g.remove_node(node.node_id)

    def get_node(self, node_id):
        return self.g.node[node_id]["p"]