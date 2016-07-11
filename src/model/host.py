__author__ = 'Rakesh Kumar'


class Host:

    def __init__(self, host_id, model, ip_addr, mac_addr, sw, switch_port):

        self.node_id = host_id
        self.model = model
        self.ip_addr = ip_addr
        self.mac_addr = mac_addr

        self.sw = sw
        self.switch_port = switch_port

        self.port_graph_ingress_node = None
        self.port_graph_egress_node = None
