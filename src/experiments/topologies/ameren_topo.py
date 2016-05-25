__author__ = 'Rakesh Kumar'

from mininet.topo import Topo

class AmerenTopo(Topo):

    '''
    Switch	    Display Name
    ------      -------------
        1	        NW
        2   	    NE
        3	        SW
        4	        SE

    Hostname short-hand:
    The host with IP 192.168.1.x is named as hx

    '''

    def __init__(self):
        
        Topo.__init__(self)


        self.num_switches = 4
        self.total_switches = self.num_switches
        self.switch_names = []

        # Add switches
        for i in xrange(self.num_switches):
            curr_switch = self.addSwitch("s" + str(i+1), protocols="OpenFlow14")
            self.switch_names.append(curr_switch)

        # Add Links

        #  Four switches in the ring
        self.addLink('s1', 's2', port1=1, port2=1)
        self.addLink('s2', 's4', port1=2, port2=2)
        self.addLink('s4', 's3', port1=1, port2=1)
        self.addLink('s1', 's3', port1=2, port2=2)

        # Diagonal links
        self.addLink('s2', 's3', port1=3, port2=3)
        self.addLink('s4', 's1', port1=3, port2=3)


        # Add other devices (as hosts in the mininet) and their links to switches they connect at
        self.addHost('h10')
        self.addLink('s1', 'h10', port1=5, port2=0)

        self.addHost('h30')
        self.addLink('s1', 'h30', port1=6, port2=0)
        self.addLink('s2', 'h30', port1=6, port2=1)

        self.addHost('h41')
        self.addLink('s2', 'h41', port1=5, port2=0)

        self.addHost('h20')
        self.addLink('s4', 'h20', port1=6, port2=0)

        self.addHost('h1')
        self.addLink('s3', 'h1', port1=5, port2=0)

        self.addHost('h100')
        self.addLink('s4', 'h100', port1=5, port2=0)

topos = {"amerentopo": (lambda: AmerenTopo())}
