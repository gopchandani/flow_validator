__author__ = 'Rakesh Kumar'


class Host():

    def __init__(self, host_id, model, ip_addr, mac_addr=None, switch_id=None):

        self.host_id = host_id
        self.model = model
        self.ip_addr = ip_addr
        self.mac_addr = mac_addr
        self.switch_id = switch_id
