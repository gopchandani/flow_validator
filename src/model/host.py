__author__ = 'Rakesh Kumar'


class Host:

    def __init__(self, host_id, model, ip_addr, mac_addr, sw, switch_port):

        self.node_id = host_id
        self.model = model
        self.ip_addr = ip_addr
        self.mac_addr = mac_addr
        self.mac_addr_int = int(self.mac_addr.replace(":", ""), 16)

        self.sw = sw
        self.switch_port = switch_port

        if switch_port:
            self.generate_ingress_egress_node_ids()

    def generate_ingress_egress_node_ids(self):
        self.port_graph_ingress_node_id = self.sw.node_id + ":ingress" + str(self.switch_port.port_number)
        self.port_graph_egress_node_id = self.sw.node_id + ":egress" + str(self.switch_port.port_number)
