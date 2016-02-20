__author__ = 'Rakesh Kumar'

import networkx as nx

from traffic import Traffic

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

    def predecessors_iter(self, node):
        for pred_id in self.g.predecessors_iter(node.node_id):
            yield self.get_node(pred_id)

    def successors_iter(self, node):
        for succ_id in self.g.successors_iter(node.node_id):
            yield self.get_node(succ_id)

    def add_edge(self, pred, succ, edge_data):
        self.g.add_edge(pred.node_id, succ.node_id, e=edge_data)

    def remove_edge(self, pred, succ):

        edge_to_remove = self.get_edge(pred, succ)

        # First check if the edge exists
        if edge_to_remove:

            # Remove the port-graph edges corresponding to ports themselves
            self.g.remove_edge(pred.node_id, succ.node_id)

        return edge_to_remove

    def get_edge(self, pred, succ):

        if self.g.has_edge(pred.node_id, succ.node_id):
            return self.g.get_edge_data(pred.node_id, succ.node_id)["e"]
        else:
            return None

    def get_admitted_traffic(self, node, dst):

        dst_admitted_traffic = Traffic()

        if dst in node.admitted_traffic:
            for succ in node.admitted_traffic[dst]:
                dst_admitted_traffic.union(node.admitted_traffic[dst][succ])

        return dst_admitted_traffic

    def get_transfer_traffic(self, node, dst):

        dst_transfer_traffic = Traffic()

        if dst in node.transfer_traffic:
            for succ in node.transfer_traffic[dst]:
                dst_transfer_traffic.union(node.transfer_traffic[dst][succ])

        return dst_transfer_traffic

    def get_transfer_traffic_via_succ(self, node, dst, succ):
        return node.transfer_traffic[dst][succ]

    def set_transfer_traffic_via_succ(self, node, dst, succ, transfer_traffic):
        node.transfer_traffic[dst][succ] = transfer_traffic

    def get_transfer_traffic_dsts(self, node):
        return node.transfer_traffic.keys()

    def get_transfer_traffic_succ(self, node, dst):
        succ_list = None
        if dst in node.transfer_traffic:
            succ_list = node.transfer_traffic[dst].keys()

        return succ_list

