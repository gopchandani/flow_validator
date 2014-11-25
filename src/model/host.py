__author__ = 'Rakesh Kumar'


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

        #Analysis stuff
        self.in_port_match = None

    def transfer_function(self, in_port_match):
        # Dont know the port on the host side, using 0
        return {0: in_port_match}
