__author__ = 'Rakehs Kumar'

from mininet.topo import Topo

class ClosTopo(Topo):

    def __init__(self, fanout, cores, **opts):
        
        # Initialize topology and default options
        Topo.__init__(self, **opts)

        self.total_core_switches = cores
        self.total_agg_switches = self.total_core_switches * fanout
        self.total_edge_switches = self.total_agg_switches * fanout

        self.total_switches = 0

        core_switches = {}

        for x in range(1, self.total_core_switches + 1):
            self.total_switches += 1
            core_switches[x] = self.addSwitch('s%i' % self.total_switches, protocols="OpenFlow13")
            
        print "Core switches:", core_switches
        
        agg_switches = {}
        for x in range(1, self.total_agg_switches + 1):
            self.total_switches += 1
            agg_switches[x] = self.addSwitch('s%i' % self.total_switches, protocols="OpenFlow13")
            
        print "Aggregate switches:", agg_switches

        for x in core_switches:
            for y in agg_switches:
                self.addLink(core_switches[x], agg_switches[y])

        edge_switches = {}
        for x in range(1, self.total_edge_switches + 1):
            self.total_switches += 1
            edge_switches[x] = self.addSwitch('s%i' % self.total_switches, protocols="OpenFlow13")
            
        print "Edge switches:",  edge_switches

        for x in agg_switches:
            for y in edge_switches:
                self.addLink(agg_switches[x], edge_switches[y])

        for edge_switch_num in edge_switches:
            
            # add fanout number of hosts to each edge switch
            for y in xrange(fanout):
                host_name = self.addHost("h" + edge_switches[edge_switch_num][1:] + str(y+1))
                self.addLink(host_name, edge_switches[edge_switch_num])

topos = {"clostopo": (lambda: ClosTopo())}
