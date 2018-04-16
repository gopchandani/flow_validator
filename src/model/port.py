__author__ = 'Rakesh Kumar'

from port_graph_node import PortGraphNode
from port_graph import PortGraph
from traffic import Traffic


class Port(object):

    def __init__(self, sw, port_raw):

        self.sw = sw
        self.port_id = None
        self.curr_speed = None
        self.max_speed = None

        self.mac_address = None
        self.port_number = None
        self.state = None
        self.attached_host = None

        if self.sw.network_graph.controller == "ryu":
            self.parse_ryu_port_json(port_raw)

        elif self.sw.network_graph.controller == "onos":
            self.parse_onos_port_json(port_raw)

        elif self.sw.network_graph.controller == "grpc":
            self.parse_grpc_port(port_raw)
        else:
            raise NotImplemented

    def init_port_graph_state(self):

        # Need port_number parsed in before this is called
        self.switch_port_graph_ingress_node = PortGraphNode(self.sw,
                                                            PortGraph.get_ingress_node_id(self.sw.node_id,
                                                                                          self.port_number),
                                                            "ingress")

        self.switch_port_graph_egress_node = PortGraphNode(self.sw,
                                                           PortGraph.get_egress_node_id(self.sw.node_id,
                                                                                        self.port_number),
                                                           "egress")

        self.network_port_graph_ingress_node = PortGraphNode(self.sw,
                                                             PortGraph.get_ingress_node_id(self.sw.node_id,
                                                                                           self.port_number),
                                                             "ingress")

        self.network_port_graph_egress_node = PortGraphNode(self.sw,
                                                            PortGraph.get_egress_node_id(self.sw.node_id,
                                                                                         self.port_number),
                                                            "egress")

        self.switch_port_graph_ingress_node.parent_obj = self
        self.switch_port_graph_egress_node.parent_obj = self
        self.network_port_graph_ingress_node.parent_obj = self
        self.network_port_graph_egress_node.parent_obj = self

        self.ingress_node_traffic = Traffic(init_wildcard=True)
        self.ingress_node_traffic.set_field("in_port", int(self.port_number))

    def parse_odl_port_json(self, port_raw):

        self.port_id = str(self.sw.node_id) + ":" + str(port_raw["flow-node-inventory:port-number"])
        self.port_number = port_raw["flow-node-inventory:port-number"]
        self.mac_address = port_raw["flow-node-inventory:hardware-address"]
        self.curr_speed = int(port_raw["flow-node-inventory:current-speed"])
        self.max_speed = int(port_raw["flow-node-inventory:maximum-speed"])

        if port_raw["flow-node-inventory:state"]["link-down"]:
            self.state = "down"
        else:
            self.state = "up"

    def parse_onos_port_json(self, port_raw):

        self.port_number = int(port_raw["port"])
        self.port_id = str(self.sw.node_id) + ":" + str(self.port_number)
        self.mac_address = None
        self.state = "up"

    def parse_ryu_port_json(self, port_raw):

        self.port_id = str(self.sw.node_id) + ":" + str(port_raw["port_no"])
        self.port_number = port_raw["port_no"]
        self.mac_address = port_raw["hw_addr"]

        if "curr_speed" in port_raw:
            self.curr_speed = int(port_raw["curr_speed"])
        if "max_speed" in port_raw:
            self.max_speed = int(port_raw["max_speed"])

        self.state = "up"

    def parse_grpc_port(self, port_raw):
        self.port_id = str(self.sw.node_id) + ":" + str(port_raw.port_num)
        self.port_number = port_raw.port_num
        self.mac_address = port_raw.port_num

        self.state = "up"

    def __str__(self):
        return str(self.port_id)

    def __repr__(self):
        return str(self.port_id)
