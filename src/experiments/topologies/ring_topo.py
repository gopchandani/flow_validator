__author__ = 'Rakesh Kumar'

from mininet.topo import Topo

class RingTopo(Topo):
    
    def __init__(self, num_switches=4, num_hosts_per_switch=1):
        
        Topo.__init__(self)

        self.num_switches = num_switches
        self.total_switches = self.num_switches
        self.num_hosts_per_switch = num_hosts_per_switch
        self.switch_names = []

        #  Add switches and hosts under them
        for i in xrange(self.num_switches):
            curr_switch = self.addSwitch("s" + str(i+1), protocols="OpenFlow13")
            self.switch_names.append(curr_switch)

            if curr_switch == 's1' or curr_switch == 's5':
                pass
            else:
                continue

            for j in xrange(self.num_hosts_per_switch):
                curr_switch_host = self.addHost("h" + str(i+1) + str(j+1))
                self.addLink(curr_switch, curr_switch_host)

        #  Add links between switches
        if self.num_switches > 1:
            for i in xrange(self.num_switches - 1):
                self.addLink(self.switch_names[i], self.switch_names[i+1])

            #  Form a ring only when there are more than two switches
            if self.num_switches > 2:
                self.addLink(self.switch_names[0], self.switch_names[-1])

topos = {"ringtopo": (lambda: RingTopo())}
