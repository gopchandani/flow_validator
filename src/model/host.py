__author__ = 'Rakesh Kumar'

from port import Port

class Host():

    def __init__(self, host_id, model, ip_addr, mac_addr=None, switch_id=None, switch_obj=None, switch_port_attached=None):

        self.node_id = host_id
        self.model = model
        self.ip_addr = ip_addr
        self.mac_addr = mac_addr

        self.switch_id = switch_id
        self.switch_obj = switch_obj

        self.switch_port_attached = switch_port_attached
        self.switch_port = switch_obj.ports[self.switch_port_attached]

        self.switch_ingress_port  = None

        self.switch_egress_port = None

        self.port = Port(None, port_type="host", port_id=self.node_id)

