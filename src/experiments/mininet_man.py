__author__ = 'Rakesh Kumar'


import time
import os
from functools import partial


from mininet.topo import LinearTopo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.node import OVSSwitch
from model.network_graph import NetworkGraph

from experiments.topologies.fat_tree import FatTree
from experiments.topologies.two_ring_topo import TwoRingTopo
from experiments.topologies.ring_topo import RingTopo

from synthesis.synthesize_dij import SynthesizeDij


class MininetMan():

    def __init__(self,
                 controller_port,
                 topo_name,
                 num_switches,
                 num_hosts_per_switch):

        self.net = None
        self.ping_timeout = 5
        self.num_switches = num_switches
        self.num_hosts_per_switch = num_hosts_per_switch
        self.controller_port = int(controller_port)

        self.experiment_switches = None
        self.topo_name = topo_name

        if self.topo_name == "ring":
            self.topo = RingTopo(self.num_switches, self.num_hosts_per_switch)
        elif self.topo_name == "linear":
            self.topo = LinearTopo(self.num_switches, self.num_hosts_per_switch)
        elif self.topo_name == "two_ring":
            self.topo = TwoRingTopo(self.num_switches, self.num_hosts_per_switch)
        elif self.topo_name == "fat_tree":
            self.topo = FatTree(self.num_switches, self.num_hosts_per_switch)
        else:
            raise Exception("Invalid, unknown topology type: " % topo_name)

        self.switch = partial(OVSSwitch, protocols='OpenFlow13')

        self.net = Mininet(topo=self.topo,
                           cleanup=True,
                           autoStaticArp=True,
                           controller=lambda name: RemoteController(name, ip='127.0.0.1', port=self.controller_port),
                           switch=self.switch)

    def get_all_switch_hosts(self, switch_id):

        p = self.topo.ports

        for node in p:

            # Only look for this switch's hosts
            if node != switch_id:
                continue

            for switch_port in p[node]:
                dst_list = p[node][switch_port]
                dst_node = dst_list[0]
                if dst_node.startswith("h"):
                    yield self.net.get(dst_node)





    def get_experiment_switch_hosts(self, switch_id):

        if switch_id in self.experiment_switches:
            for i in range(0, self.num_hosts_per_switch):
                host_name = "h" + switch_id[1:] + str(i+1)
                yield self.net.get(host_name)
        else:
            return

    def _get_experiment_host_pair(self):

        for src_switch in self.experiment_switches:
            for dst_switch in self.experiment_switches:
                if src_switch == dst_switch:
                    continue

                # Assume one host per switch
                src_host = "h" + src_switch[1:] + "1"
                dst_host = "h" + dst_switch[1:] + "1"

                src_host_node = self.net.get(src_host)
                dst_host_node = self.net.get(dst_host)

                yield (src_host_node, dst_host_node)

    def _ping_host_pair(self, src_host, dst_host):
        hosts = [src_host, dst_host]
        ping_loss_rate = self.net.ping(hosts, self.ping_timeout)
        print "Ping Loss Rate:", ping_loss_rate

        if ping_loss_rate < 100.0:
            return True
        else:
            return False

    def _ping_experiment_hosts(self):

        if self.topo_name == "line":
            self.net.pingAll(timeout=self.ping_timeout)
        else:
            for (src_host, dst_host) in self._get_experiment_host_pair():
                self._ping_host_pair(src_host, dst_host)

    def setup_mininet_with_odl(self):

        # Start
        self.net.start()

        print "Waiting for the controller to get ready for synthesis"
        time.sleep(180)

        print "Synthesizing..."

        self.ng = NetworkGraph(mininet_man=self)
        self.synthesis_dij = SynthesizeDij(self.ng, master_switch=self.topo_name == "line")
        self.synthesis_dij.synthesize_all_node_pairs()

        print "Synthesis Completed. Waiting for rules to be detected by controller..."
        time.sleep(30 * self.num_hosts_per_switch * self.num_switches)

    def setup_mininet_with_ryu(self):
        pass

    def cleanup_mininet(self):

        if self.net:
            print "Mininet cleanup..."
            self.net.stop()
            os.system("sudo mn -c")

    def __del__(self):
        self.cleanup_mininet()

def main():

    topo_description = ("ring", 4, 1)
    mm = MininetMan(6633, *topo_description)
    mm.net.start()
    mm.net.pingAll()

if __name__ == "__main__":
    main()