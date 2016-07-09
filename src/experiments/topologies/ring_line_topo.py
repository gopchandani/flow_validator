__author__ = 'Rakesh Kumar'

from mininet.topo import Topo

class RingLineTopo(Topo):
    '''
    Creates topologies that look like the following:
                    o       
                  /  \
    o-o-o - ... o     o - o
                 \   /
                  o
    
    It is a line with a ring placed right in the middle of it.
    The number of switches in the ring and the number of switches form the left side line 
    
    '''
            
    def __init__(self, num_switches, num_hosts_per_switch):
        
        Topo.__init__(self)

        self.num_ring_switches = 4
        self.num_left_line_switches = (num_switches - 5)

        self.total_switches = num_switches
        self.num_hosts_per_switch = num_hosts_per_switch

        self.ring_switch_names = []
        self.left_line_switch_names = []
        self.target_switch_name = ''

        #  Add ring switches and hosts under them
        for i in xrange(self.num_ring_switches):
            switch_name = self.add_switch_and_host(i+1)
            self.ring_switch_names.append(switch_name)

        #  Add links between ring switches
        if self.num_ring_switches > 1:
            for i in xrange(self.num_ring_switches - 1):
                self.addLink(self.ring_switch_names[i], self.ring_switch_names[i+1])

            #  Form a ring only when there are more than two switches
            if self.num_ring_switches > 2:
                self.addLink(self.ring_switch_names[0], self.ring_switch_names[-1])
                
        # Add left line switches along with links
        i = self.num_ring_switches + 1
        to_link_switch_name = 's1'
        while i <= self.num_left_line_switches + self.num_ring_switches:
            this_switch_name = self.add_switch_and_host(i)
            self.addLink(this_switch_name, to_link_switch_name)

            self.left_line_switch_names.append(this_switch_name)
            to_link_switch_name = this_switch_name
            i += 1

        # Add the target switch and attach it to other side of ring, halfway from s1 in the ring
        self.target_switch_name = self.add_switch_and_host(i)
        self.addLink(self.target_switch_name, 's' + str(self.num_ring_switches/2 + 1))

    def add_switch_and_host(self, switch_num):
    
        switch_name = self.addSwitch("s" + str(switch_num), protocols="OpenFlow14")

        for j in xrange(self.num_hosts_per_switch):
            host_name = self.addHost("h" + str(switch_num) + str(j+1))
            self.addLink(switch_name, host_name)
        
        return switch_name

topos = {"ringline": (lambda: RingLineTopo())}
