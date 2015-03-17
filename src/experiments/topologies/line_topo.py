__author__ = 'Rakesh Kumar'

from mininet.topo import Topo

class LineTopo(Topo):
    
    def __init__(self, num_switches, num_hosts_per_switch):
        
        Topo.__init__(self)
        
        self.num_switches = num_switches
        self.total_switches = self.num_switches
        self.num_hosts_per_switch = num_hosts_per_switch
        switches = []

        #  Add switches and hosts under them
        for i in range(self.num_switches):
            curr_switch = self.addSwitch("s" + str(i+1), protocols="OpenFlow13")
            switches.append(curr_switch)

            for j in range(self.num_hosts_per_switch):
                curr_switch_host = self.addHost("h" + str(i) + str(j))
                self.addLink(curr_switch, curr_switch_host)

        #  Add links between switches
        if self.num_switches > 1:
            for i in range(self.num_switches - 1):
                self.addLink(switches[i], switches[i+1])


topos = {"linetopo": (lambda: LineTopo())}