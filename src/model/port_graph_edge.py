__author__ = 'Rakesh Kumar'

class PortGraphEdge():

    def __init__(self, port1, port2):

        self.port1 = port1
        self.port2 = port2

        self.edge_type = None

        if (port1.node_type == "table") and (port2.node_type == "egress"):
            self.edge_type = "egress"
        elif (port1.node_type == "ingress") and (port2.node_type == "table"):
            self.edge_type = "ingress"
        elif (port1.node_type == "egress") and (port2.node_type == "ingress"):
            self.edge_type = "outside"
        elif (port1.node_type == "ingress") and (port2.node_type == "egress"):
            self.edge_type = "inside"

        self.edge_data_list = []

    def add_edge_data(self, edge_data):
        self.edge_data_list.append(edge_data)


class NetworkPortGraphEdgeData():

    def __init__(self, edge_filter_traffic, modifications, vuln_rank):

        self.edge_filter_traffic = edge_filter_traffic
        self.modifications = modifications
        self.vuln_rank = vuln_rank

class SwitchPortGraphEdgeData():

    def __init__(self, edge_filter_traffic, edge_action, applied_modifications, written_modifications):

        self.edge_filter_traffic = edge_filter_traffic
        self.edge_action = edge_action
        self.applied_modifications = applied_modifications
        self.written_modifications = written_modifications