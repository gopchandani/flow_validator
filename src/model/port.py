__author__ = 'Rakesh Kumar'

from model.traffic import Traffic
from collections import defaultdict

class Port():

    def __init__(self, sw, port_json=None, port_type="physical", port_id=None):

        self.sw = sw
        self.port_type = port_type
        self.port_id = None
        self.curr_speed = None
        self.max_speed = None

        # This nested dictionary is to hold Traffic object per successor, per destination
        self.transfer_traffic = defaultdict(defaultdict)
        self.admitted_traffic = defaultdict(defaultdict)

        # These apply specifically to physical ports
        self.mac_address = None
        self.port_number = None
        self.state = None

        if port_type == "physical" and self.sw.network_graph.controller == "odl":
            self.parse_odl_port_json(port_json)

        elif port_type == "physical" and self.sw.network_graph.controller == "ryu":
            self.parse_ryu_port_json(port_json)

        elif port_type == "ingress":
            self.port_id = port_id
        elif port_type == "egress":
            self.port_id = port_id
        elif port_type == "table":
            self.port_id = port_id
        elif port_type == "controller":
            self.port_id = port_id

        else:
            raise Exception("Invalid port type specified.")

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

    def parse_odl_port_json(self, port_json):

        self.port_id = str(self.sw.node_id) + ":" + str(port_json["flow-node-inventory:port-number"])
        self.port_number = port_json["flow-node-inventory:port-number"]
        self.mac_address = port_json["flow-node-inventory:hardware-address"]
        self.curr_speed = int(port_json["flow-node-inventory:current-speed"])
        self.max_speed = int(port_json["flow-node-inventory:maximum-speed"])

        if port_json["flow-node-inventory:state"]["link-down"]:
            self.state = "down"
        else:
            self.state = "up"

    def parse_ryu_port_json(self, port_json):

        self.port_id = str(self.sw.node_id) + ":" + str(port_json["port_no"])
        self.port_number = port_json["port_no"]
        self.mac_address = port_json["hw_addr"]

        if "curr_speed" in port_json:
            self.curr_speed = int(port_json["curr_speed"])
        if "max_speed" in port_json:
            self.max_speed = int(port_json["max_speed"])

        #TODO: Peep into port_json["state"]
        self.state = "up"

    def __str__(self):

        return " Id: " + str(self.port_id)
