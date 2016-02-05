__author__ = 'Rakesh Kumar'

from collections import defaultdict
from model.traffic import Traffic

class PortGraphNode:

    def __init__(self, sw, node_id, node_type):

        if node_type in ["ingress", "egress", "table", "controller"]:

            self.sw = sw
            self.node_id = node_id
            self.node_type = node_type

            # This nested dictionary is to hold Traffic objects per successor, per destination
            self.transfer_traffic = defaultdict(defaultdict)
            self.admitted_traffic = defaultdict(defaultdict)

        else:
            raise Exception("Invalid port type specified.")

    def __str__(self):

        return " Id: " + str(self.node_id)

    def get_dst_admitted_traffic(self, dst_p):

        dst_admitted_traffic = Traffic()

        if dst_p in self.admitted_traffic:
            for succ in self.admitted_traffic[dst_p]:
                dst_admitted_traffic.union(self.admitted_traffic[dst_p][succ])

        return dst_admitted_traffic


    def get_dst_transfer_traffic(self, dst_p):

        dst_transfer_traffic = Traffic()

        if dst_p in self.transfer_traffic:
            for succ in self.transfer_traffic[dst_p]:
                dst_transfer_traffic.union(self.transfer_traffic[dst_p][succ])

        return dst_transfer_traffic