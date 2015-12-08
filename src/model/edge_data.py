__author__ = 'Rakesh Kumar'


class EdgeData():

    def __init__(self, port1, port2):

        self.port1 = port1
        self.port2 = port2

        self.edge_type = None

        if (port1.port_type == "table") and (port2.port_type == "egress"):
            self.edge_type = "egress"
        elif (port1.port_type == "ingress") and (port2.port_type == "table"):
            self.edge_type = "ingress"

        elif (port1.port_type == "egress") and (port2.port_type == "ingress"):
            self.edge_type = "outside"
        elif (port1.port_type == "ingress") and (port2.port_type == "egress"):
            self.edge_type = "inside"

        self.edge_data_list = []

    def add_edge_data(self, edge_data_tuple):
        self.edge_data_list.append(edge_data_tuple)
