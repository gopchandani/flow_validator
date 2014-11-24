__author__ = 'Rakesh Kumar'


from netaddr import IPAddress

class Port():
    """
    Class representing a port on a switch.
    Captures the ip address assigned to the switch,
    the type of node it faces on the other side (switch/host/internal) and
    the current state (up/down) of the port

    """

    def __init__(self, sw, nc):

        self.sw = sw
        self.port_id = nc["id"]
        self.port_number = nc["flow-node-inventory:port-number"]
        self.mac_address = nc["flow-node-inventory:hardware-address"]

        self.faces = None
        self.facing_node_id = None

        if nc["flow-node-inventory:port-number"] == "LOCAL":
            self.faces = "internal"
            self.facing_node_id = self.port_id

        self.state = None

        if nc["flow-node-inventory:state"]["link-down"]:
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
