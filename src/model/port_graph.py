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

    def get_admitted_traffic_via_succ(self, node, dst, succ):
        return node.admitted_traffic[dst][succ]

    def set_admitted_traffic_via_succ(self, node, dst, succ, admitted_traffic):
        node.admitted_traffic[dst][succ] = admitted_traffic

    def get_admitted_traffic_dsts(self, node):
        return node.admitted_traffic.keys()

    def get_admitted_traffic_succs(self, node, dst):
        succ_list = None
        if dst in node.admitted_traffic:
            succ_list = node.admitted_traffic[dst].keys()

        return succ_list

    def account_node_admitted_traffic(self, curr, dst_traffic_at_succ, succ, dst):

        # Keep track of what traffic looks like before any changes occur
        traffic_before_changes = self.get_admitted_traffic(curr, dst)

        # Compute what additional traffic is being admitted overall
        additional_traffic = traffic_before_changes.difference(dst_traffic_at_succ)

        # Do the changes...
        try:
            # First accumulate any more traffic that has arrived from this sucessor
            prev_dst_traffic_at_succ = self.get_admitted_traffic_via_succ(curr, dst, succ)
            more_from_succ = prev_dst_traffic_at_succ.difference(dst_traffic_at_succ)
            if not more_from_succ.is_empty():
                prev_dst_traffic_at_succ.union(more_from_succ)

            # Then get rid of traffic that this particular successor does not admit anymore
            less_from_succ = dst_traffic_at_succ.difference(self.get_admitted_traffic_via_succ(curr, dst, succ))
            if not less_from_succ.is_empty():
                remaining = less_from_succ.difference(self.get_admitted_traffic_via_succ(curr, dst, succ))
                self.set_admitted_traffic_via_succ(curr, dst, succ, remaining)

        # If there is no traffic for this dst-succ combination prior to this propagation,
        # setup a traffic object for successor
        except KeyError:
            if not dst_traffic_at_succ.is_empty():
                new_traffic = Traffic()
                new_traffic.union(dst_traffic_at_succ)
                self.set_admitted_traffic_via_succ(curr, dst, succ, new_traffic)

        # Then see what the overall traffic looks like after additional/reduced traffic for specific successor
        traffic_after_changes = self.get_admitted_traffic(curr, dst)

        # Compute what reductions (if any) in traffic has occured due to all the changes
        reduced_traffic = traffic_after_changes.difference(traffic_before_changes)

        traffic_to_propagate = traffic_after_changes

        return additional_traffic, reduced_traffic, traffic_to_propagate