__author__ = 'Rakesh Kumar'


class EdgeData():

    def __init__(self, port1, port2):

        self.port1 = port1
        self.port2 = port2

        self.edge_type = None
        if (self.port1.port_type == "table" or self.port1.port_type == "ingress") and (self.port2.port_type == "egress"):
            self.edge_type = "egress"
        elif (self.port1.port_type == "ingress") and (self.port2.port_type == "table" or self.port2.port_type == "egress"):
            self.edge_type = "ingress"

        self.edge_data_list = []

    def add_edge_data(self, edge_data_tuple):
        self.edge_data_list.append(edge_data_tuple)
