__author__ = 'Rakesh Kumar'


class Host:

    def __init__(self, host_id, model, ip_addr, mac_addr=None, switch_id=None, switch_obj=None, switch_port=None):

        self.node_id = host_id
        self.model = model
        self.ip_addr = ip_addr
        self.mac_addr = mac_addr

        self.switch_id = switch_id
        self.switch_obj = switch_obj

        self.switch_port = switch_port
        self.switch_port.attached_host = self

        self.port_graph_ingress_node = None
        self.port_graph_egress_node = None

    def get_switch_port(self):
        self.switch_port.attached_host = self
        return self.switch_port
