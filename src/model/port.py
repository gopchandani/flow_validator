__author__ = 'Rakesh Kumar'


from netaddr import IPAddress

class Port():
    """
    Class representing a port on a switch.
    Captures the ip address assigned to the switch,
    the type of node it faces on the other side (switch/host/internal) and
    the current state (up/down) of the port

    """

    def __init__(self, nc):

        self.id = nc["id"]
        self.mac_address = nc["flow-node-inventory:hardware-address"]

        self.faces = None
        if nc["flow-node-inventory:port-number"] == "LOCAL":
            self.faces = "internal"
        elif "address-tracker:addresses" in nc:
            self.faces = "host"
        else:
            self.faces = "switch"

        self.state = None
        if nc["flow-node-inventory:state"]["link-down"]:
            self.state = "down"
        else:
            self.state = "up"