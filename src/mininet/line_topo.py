__author__ = 'Rakesh Kumar'

from mininet.topo import Topo

class LineTopo(Topo):
    
    def __init__(self):
        
        Topo.__init__(self)
        
        num_switches = 3
        num_hosts_per_switch = 1
        switches = []

        #  Add switches and hosts under them
        for i in range(num_switches):
            curr_switch = self.addSwitch("s" + str(i))
            switches.append(curr_switch)

            for j in range(num_hosts_per_switch):
                curr_switch_host = self.addHost("h" + str(i) + str(j))
                self.addLink(curr_switch, curr_switch_host)

        #  Add links between switches
        if num_switches > 1:
            for i in range(num_switches - 1):
                print switches[i], type(switches[i])
                self.addLink(switches[i], switches[i+1])


topos = {"linetopo": (lambda: LineTopo())}
