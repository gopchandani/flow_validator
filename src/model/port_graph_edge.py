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

    def __init__(self, edge_filter_traffic, modifications, switch_port_graph_paths):

        self.edge_filter_traffic = edge_filter_traffic
        self.modifications = modifications
        self.switch_port_graph_paths = switch_port_graph_paths

    def get_vuln_rank(self):

        # If it is an edge that does not depend on switch_port_graph_paths, then say zero
        if self.switch_port_graph_paths == None:
            return 0

        # Do a min over paths for getting vuln_rank
        min_vuln_rank = 100000
        for tp in self.switch_port_graph_paths:
            path_max_vuln_rank = tp.get_max_vuln_rank()
            if path_max_vuln_rank < min_vuln_rank:
                min_vuln_rank = path_max_vuln_rank

        return min_vuln_rank

    def get_active_rank(self):

        # If it is an edge that does not depend on switch_port_graph_paths, then say zero
        if self.switch_port_graph_paths == None:
            return 0

        # Do a max over paths for getting active_rank
        max_active_rank= -1
        for tp in self.switch_port_graph_paths:
            path_max_active_rank = tp.get_max_active_rank()
            if path_max_active_rank > max_active_rank:
                max_active_rank = path_max_active_rank

        return max_active_rank

class SwitchPortGraphEdgeData():

    def __init__(self, edge_filter_traffic, edge_action, applied_modifications, written_modifications):

        self.edge_filter_traffic = edge_filter_traffic
        self.edge_action = edge_action
        self.applied_modifications = applied_modifications
        self.written_modifications = written_modifications

    def get_vuln_rank(self):
        if self.edge_action:
            return self.edge_action.vuln_rank
        else:
            return 0

    def get_active_rank(self):
        if self.edge_action:
            return self.edge_action.get_active_rank()
        else:
            return 0