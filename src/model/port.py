__author__ = 'Rakesh Kumar'

from port_graph_node import PortGraphNode

class Port():

    def __init__(self, sw, port_json):

        self.sw = sw
        self.port_id = None
        self.curr_speed = None
        self.max_speed = None

        self.mac_address = None
        self.port_number = None
        self.state = None

        if self.sw.network_graph.controller == "odl":
            self.parse_odl_port_json(port_json)

        elif self.sw.network_graph.controller == "ryu":
            self.parse_ryu_port_json(port_json)


        # Need port_number parsed in before this is called
        self.port_graph_ingress_node = PortGraphNode(self.sw,
                                                     self.sw.port_graph.get_ingress_node_id(self.sw.node_id,
                                                                                            self.port_number),
                                                     "ingress")

        self.port_graph_egress_node = PortGraphNode(self.sw,
                                                    self.sw.port_graph.get_egress_node_id(self.sw.node_id,
                                                                                          self.port_number),
                                                    "egress")

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

        return str(self.port_id)
