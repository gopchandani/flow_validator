__author__ = 'Rakesh Kumar'


class PortGraphEdge:

    def __init__(self, pred, succ):

        self.pred = pred
        self.succ = succ

        self.edge_type = None

        if (pred.node_type == "table") and (succ.node_type == "egress"):
            self.edge_type = "egress"
        elif (pred.node_type == "ingress") and (succ.node_type == "table"):
            self.edge_type = "ingress"
        elif (pred.node_type == "egress") and (succ.node_type == "ingress"):
            self.edge_type = "outside"
        elif (pred.node_type == "ingress") and (succ.node_type == "egress"):
            self.edge_type = "inside"

        self.edge_data_list = []

    def add_edge_data(self, edge_data):
        self.edge_data_list.append(edge_data)

    def get_max_active_rank(self):
        max_active_rank = -1
        for enabling_edge_data in self.edge_data_list:
            current_edge_data_active_rank = enabling_edge_data.get_active_rank()
            if current_edge_data_active_rank > max_active_rank:
                max_active_rank = current_edge_data_active_rank
        return max_active_rank


class NetworkPortGraphEdgeData:

    def __init__(self, edge_filter_traffic, applied_modifications, switch_port_graph_paths):

        self.edge_filter_traffic = edge_filter_traffic
        self.applied_modifications = applied_modifications
        self.switch_port_graph_paths = switch_port_graph_paths

    def get_active_rank(self):

        # If it is an edge that does not depend on switch_port_graph_paths, then say zero
        if self.switch_port_graph_paths == None:
            return 0

        # Do a max over paths for getting active_rank
        max_active_rank = -1
        for tp in self.switch_port_graph_paths:
            path_max_active_rank = tp.get_max_active_rank()
            if path_max_active_rank > max_active_rank:
                max_active_rank = path_max_active_rank

        return max_active_rank

    def get_min_active_rank(self):

        # If it is an edge that does not depend on switch_port_graph_paths, then say zero
        if self.switch_port_graph_paths == None:
            return 0

        # Do a max over paths for getting active_rank
        min_active_rank = 100000
        for tp in self.switch_port_graph_paths:
            path_max_active_rank = tp.get_max_active_rank()
            if path_max_active_rank < min_active_rank:
                min_active_rank = path_max_active_rank

        return min_active_rank


class SwitchPortGraphEdgeData:

    def __init__(self, edge_filter_traffic, edge_action, applied_modifications, written_modifications):

        self.edge_filter_traffic = edge_filter_traffic
        self.edge_action = edge_action
        self.applied_modifications = applied_modifications
        self.written_modifications = written_modifications

    def get_active_rank(self):
        if self.edge_action:
            print "  has edge_action"
            return self.edge_action.get_active_rank()
        else:
            return -1
