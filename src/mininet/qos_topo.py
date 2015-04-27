s__author__ = 'Rakesh Kumar'

from mininet.topo import Topo

class QosTopo(Topo):
    
    def __init__(self):
        
        Topo.__init__(self)
    
        self.num_switches = 2
        self.num_hosts_per_switch = 1
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


topos = {"qostopo": (lambda: QosTopo())}
