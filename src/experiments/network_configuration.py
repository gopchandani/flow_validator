__author__ = 'Rakesh Kumar'

class NetworkConfiguration():

    def __init__(self, synthesis_scheme, controller_port, topo_name, num_switches, num_hosts_per_switch, fanout, core, per_switch_links, dst_ports_to_synthesize):

        self. synthesis_scheme = synthesis_scheme
        self.controller_port = controller_port
        self.topo_name = topo_name
        self.num_switches = num_switches
        self.num_hosts_per_switch = num_hosts_per_switch
        self.fanout = fanout
        self.core = core
        self.per_switch_links = per_switch_links
        self.dst_ports_to_synthesize = dst_ports_to_synthesize

    def __str__(self):
        pass