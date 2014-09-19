__author__ = 'Rakesh Kumar'

from mininet.topo import Topo


class BackupTopo(Topo):
    def __init__(self):
        Topo.__init__(self)

        host1 = self.addHost("h1")
        host2 = self.addHost("h2")
        host3 = self.addHost("h3")
        host4 = self.addHost("h4")

        l0 = self.addSwitch("l0")
        l10 = self.addSwitch("l10")
        l11 = self.addSwitch("l11")
        l20 = self.addSwitch("l20")
        l21 = self.addSwitch("l21")

        # Hosts/Leafs to switches
        self.addLink(host1, l20)
        self.addLink(host2, l20)
        self.addLink(host3, l21)
        self.addLink(host4, l21)

        #  Bottom-Middle layer
        self.addLink(l10, l20)
        self.addLink(l10, l21)
        self.addLink(l11, l20)
        self.addLink(l11, l21)

        #  Middle-Top Layer
        self.addLink(l11, l0)
        self.addLink(l10, l0)


topos = {"backuptopo": ( lambda: BackupTopo() )}
