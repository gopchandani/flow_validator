__author__ = 'Rakesh Kumar'


from netaddr import IPAddress

class Port():
    """
    Class representing a port on a switch.
    Captures the ip address assigned to the switch,
    the type of node it faces on the other side (switch/host/internal) and
    the current state (up/down) of the port

    """

    def __init__(self, sw, node_connector_json=None, port_type="physical", port_id=None):

        self.sw = sw
        self.port_type = port_type
        self.port_id = None

        # This dictionary is to hold a Match object per destination
        self.destination_match = {}


        # These apply specifically to physical ports
        self.mac_address = None
        self.port_number = None
        self.faces = None
        self.facing_node_id = None
        self.state = None

        if port_type == "physical" and node_connector_json:
            self._populate_with_node_connector_json(node_connector_json)
        elif port_type == "table":
            self.port_id = port_id
        elif port_type == "controller":
            self.port_id = port_id
        else:
            raise Exception("Invalid port type specified.")

    def _populate_with_node_connector_json(self, node_connector_json):
        self.port_id = node_connector_json["id"]
        self.port_number = node_connector_json["flow-node-inventory:port-number"]
        self.mac_address = node_connector_json["flow-node-inventory:hardware-address"]

        if node_connector_json["flow-node-inventory:port-number"] == "LOCAL":
            self.faces = "internal"
            self.facing_node_id = self.port_id

        if node_connector_json["flow-node-inventory:state"]["link-down"]:
            self.state = "down"
        else:
            self.state = "up"

    def __str__(self):

        return "Port -- " + \
               " Id: " + str(self.port_id) + \
               " Port Number: " + str(self.port_number) + \
               " MAC Address: " + str(self.mac_address) + \
               " Faces: " + str(self.faces) + \
               " Facing Node Id: " + str(self.facing_node_id) + \
               " State:" + str(self.state)
