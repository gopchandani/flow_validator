__author__ = 'Rakesh Kumar'

from mininet.topo import Topo


class WSCTopo(Topo):

    def __init__(self, params):
        Topo.__init__(self)
        self.params = params
        self.total_switches = self.params["num_switches"]
        self.switch_names = []

        self.build_topo()

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
            self.addLink("s" + str(e[0]+1), "s" + str(e[1]+1))
