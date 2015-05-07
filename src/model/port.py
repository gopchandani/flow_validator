__author__ = 'Rakesh Kumar'


class Port():

    def __init__(self, sw, port_json=None, port_type="physical", port_id=None):

        self.sw = sw
        self.port_type = port_type
        self.port_id = None

        # This dictionary is to hold a Match object per destination
        self.path_elements = {}
        self.admitted_traffic = {}
        self.traversal_distance = None

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

    def parse_odl_port_json(self, port_json):

        self.port_id = str(self.sw.node_id) + ":" + str(port_json["flow-node-inventory:port-number"])
        self.port_number = port_json["flow-node-inventory:port-number"]
        self.mac_address = port_json["flow-node-inventory:hardware-address"]

        if port_json["flow-node-inventory:state"]["link-down"]:
            self.state = "down"
        else:
            self.state = "up"

    def parse_ryu_port_json(self, port_json):

        self.port_id = str(self.sw.node_id) + ":" + str(port_json["port_no"])
        self.port_number = port_json["port_no"]
        self.mac_address = port_json["hw_addr"]

        #TODO: Peep into port_json["state"]
        self.state = "up"

    def __str__(self):

        return " Id: " + str(self.port_id)
