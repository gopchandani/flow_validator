__author__ = 'Rakesh Kumar'

from mininet.topo import Topo
from collections import defaultdict


class WSCTopo(Topo):

    def __init__(self, params):
        Topo.__init__(self)
        self.params = params
        self.total_switches = self.params["num_switches"]
        self.switch_names = []
        self.links_added = defaultdict(defaultdict)

        self.build_topo()

    def is_already_added(self, n1, n2):

        try:
            self.links_added[n1][n2]
        except KeyError:
            return False

        try:
            self.links_added[n2][n1]
        except KeyError:
            return False

        return True

    def build_topo(self):
        #  Add switches and hosts under them
        for i in xrange(self.params["num_switches"]):
            curr_switch = self.addSwitch("s" + str(i+1), protocols="OpenFlow14")
            self.switch_names.append(curr_switch)

            for j in xrange(self.params["num_hosts_per_switch"]):
                curr_switch_host = self.addHost("h" + str(i+1) + str(j+1))
                self.addLink(curr_switch, curr_switch_host)

        # Add links between the switches
        for e in self.params["edges"]:
            n1 = "s" + str(e[0]+1)
            n2 = "s" + str(e[1]+1)

            if not self.is_already_added(n1, n2):
                self.addLink(n1, n2)
                self.links_added[n1][n2] = 1
                self.links_added[n2][n1] = 1

    def __str__(self):
        params_str = ''
        for k, v in self.params.items():
            if k != "edges":
                params_str += "_" + str(k) + "_" + str(v)
        return self.__class__.__name__ + params_str
