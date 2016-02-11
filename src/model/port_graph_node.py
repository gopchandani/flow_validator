__author__ = 'Rakesh Kumar'

from collections import defaultdict
from model.traffic import Traffic

class PortGraphNode:

    def __init__(self, sw, node_id, node_type):

        if node_type in ["ingress", "egress", "table", "controller"]:

            self.sw = sw
            self.node_id = node_id
            self.node_type = node_type
            self.parent_obj = None

            # This nested dictionary is to hold Traffic objects per successor, per destination
            self.transfer_traffic = defaultdict(defaultdict)
            self.admitted_traffic = defaultdict(defaultdict)

        else:
            raise Exception("Invalid port type specified.")

    def __str__(self):

        return " Id: " + str(self.node_id)