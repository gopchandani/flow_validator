__author__ = 'Rakesh Kumar'

from mininet.topo import Topo

class TwoRingTopo(Topo):
    
    def construct_ring(self, start_offset):
        switches = []

        #  Add switches and hosts under them
        for i in range(start_offset, start_offset + self.num_switches):
            curr_switch = self.addSwitch("s" + str(i), protocols="OpenFlow13")
            switches.append(curr_switch)

            for j in range(self.num_hosts_per_switch):
                curr_switch_host = self.addHost("h" + str(i) + str(j))
                self.addLink(curr_switch, curr_switch_host)

        #  Add links between switches
        if self.num_switches > 1:
            for i in range(self.num_switches - 1):
                print switches[i], type(switches[i])
                self.addLink(switches[i], switches[i+1])

            #  Form a ring only when there are more than two switches
            if self.num_switches > 2:
                self.addLink(switches[0], switches[-1])

        return switches

    def __init__(self):
        
        Topo.__init__(self)
        
        self.num_switches = 3
        self.num_hosts_per_switch = 2

        # construct one ring
        ring1 = self.construct_ring(0)

        #construct second ring
        ring2 = self.construct_ring(self.num_switches)

        #Add a single link between the two bridges
        self.addLink(ring1[0], ring2[0])


topos = {"tworingtopo": (lambda: TwoRingTopo())}
