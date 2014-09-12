from mininet.net import Mininet
from mininet.topo import Topo

class RingTopo(Topo):
    
    def __init__(self):
        
        Topo.__init__(self)
        
        num_switches = 5
        num_hosts_per_switch = 2
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
                self.addLink(switches[i], switches[i+1])

            #  Form a ring only when there are more than two switches
            if num_switches > 2:
                self.addLink(switches[0], switches[-1])

topos = {"ringtopo" : ( lambda: RingTopo() )}
