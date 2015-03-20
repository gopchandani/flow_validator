__author__ = 'Rakesh Kumar'

from mininet.topo import Topo

class LineTopo(Topo):
    
    def __init__(self, num_switches, num_hosts_per_switch):
        
        Topo.__init__(self)
        
        self.num_switches = num_switches
        self.total_switches = self.num_switches
        self.num_hosts_per_switch = num_hosts_per_switch
        self.switch_names = []

        #  Add switches and hosts under them
        for i in range(self.num_switches):
            curr_switch = self.addSwitch("s" + str(i+1), protocols="OpenFlow13")
            self.switch_names.append(curr_switch)

            for j in range(self.num_hosts_per_switch):
                curr_switch_host = self.addHost("h" + str(i+1) + str(j+1))
                self.addLink(curr_switch, curr_switch_host)

        #  Add links between switches
        if self.num_switches > 1:
            for i in range(self.num_switches - 1):
                self.addLink(self.switch_names[i], self.switch_names[i+1])


topos = {"linetopo": (lambda: LineTopo())}
