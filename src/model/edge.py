__author__ = 'Rakesh Kumar'


class Edge():

    def __init__(self, edge_filter_match, edge_type, edge_causing_flow, edge_action):

        self.edge_filter_match = edge_filter_match
        self.edge_type = edge_type
        self.edge_causing_flow = edge_causing_flow
        self.edge_action = edge_action
