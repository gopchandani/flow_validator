__author__ = 'Rakehs Kumar'

from mininet.topo import Topo

class ClosTopo(Topo):

    def __init__(self, fanout, cores, num_hosts_per_switch, **opts):
        
        # Initialize topology and default options
        Topo.__init__(self, **opts)

        self.total_core_switches = cores
        self.total_agg_switches = self.total_core_switches * fanout
        self.total_edge_switches = self.total_agg_switches * fanout

        self.total_switches = 0
        self.num_hosts_per_switch = num_hosts_per_switch

        self.core_switches = {}
        self.agg_switches = {}
        self.edge_switches = {}

        for x in range(1, self.total_core_switches + 1):
            self.total_switches += 1
            self.core_switches[x] = self.addSwitch('s%i' % self.total_switches, protocols="OpenFlow13")
            
        print "Core switches:", self.core_switches
        
        for x in range(1, self.total_agg_switches + 1):
            self.total_switches += 1
            self.agg_switches[x] = self.addSwitch('s%i' % self.total_switches, protocols="OpenFlow13")
            
        print "Aggregate switches:", self.agg_switches

        for x in self.core_switches:
            for y in self.agg_switches:
                self.addLink(self.core_switches[x], self.agg_switches[y])

        for x in range(1, self.total_edge_switches + 1):
            self.total_switches += 1

            edge_switch_name = 's%i' % self.total_switches
            if not (edge_switch_name == 's7' or edge_switch_name == 's8' or edge_switch_name == 's9' or edge_switch_name == 's10'):
                continue

            self.edge_switches[x] = self.addSwitch('s%i' % self.total_switches, protocols="OpenFlow13")
            
        print "Edge switches:",  self.edge_switches

        for x in self.agg_switches:
            for y in self.edge_switches:
                self.addLink(self.agg_switches[x], self.edge_switches[y])

        for edge_switch_num in self.edge_switches:

            # add fanout number of hosts to each edge switch
            for y in xrange(self.num_hosts_per_switch):
                host_name = self.addHost("h" + self.edge_switches[edge_switch_num][1:] + str(y+1))
                self.addLink(host_name, self.edge_switches[edge_switch_num])

topos = {"clostopo": (lambda: ClosTopo())}
