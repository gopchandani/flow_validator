__author__ = 'Rakesh Kumar'


class NetworkConfiguration(object):

    def __init__(self, topo_name, num_switches, num_hosts_per_switch, fanout, core):

        self.topo_name = topo_name
        self.num_switches = num_switches
        self.num_hosts_per_switch = num_hosts_per_switch
        self.fanout = fanout
        self.core = core

    def __str__(self):
        if self.topo_name == "ring":
            return "Ring topology with: " + str(self.num_switches) + " switches"

        elif self.topo_name == "clostopo":
            return "Clos topology with: " + str(self.num_switches) + " switches Fanout/Core: " + str(self.fanout) + "/" + str(self.core)
