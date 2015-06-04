__author__ = 'Rakesh Kumar'


class EdgeData():

    def __init__(self, port1, port2):

        self.port1 = port1
        self.port2 = port2

        self.edge_type = None
        if (port1.port_type == "table" or port1.port_type == "ingress") and (port2.port_type == "egress"):
            self.edge_type = "egress"
        elif (port1.port_type == "ingress") and (port2.port_type == "table" or port2.port_type == "egress"):
            self.edge_type = "ingress"

        self.edge_data_list = []

    def add_edge_data(self,
                      edge_filter_match,
                      edge_causing_flow,
                      edge_action,
                      applied_modifications,
                      written_modifications,
                      output_action_type):

        self.edge_data_list.append((edge_filter_match,
                                    edge_causing_flow,
                                    edge_action,
                                    applied_modifications,
                                    written_modifications,
                                    output_action_type))

    def add_edge_data_2(self, edge_filter_traffic, modifications):
        self.edge_data_list.append((edge_filter_traffic, modifications))