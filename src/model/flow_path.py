__author__ = 'Rakesh Kumar'


class FlowPathElement():

    def __init__(self, order, node_id, port_id, match):
        self.order = order
        self.node_id = node_id
        self.port_id = port_id
        self.match = match

class FlowPath():

    def __init__(self):
        self.path_elements = []