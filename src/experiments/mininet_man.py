__author__ = 'Rakesh Kumar'


import time
import os


from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.node import OVSSwitch

from model.network_graph import NetworkGraph

from experiments.topologies.fat_tree import FatTree
from experiments.topologies.two_ring_topo import TwoRingTopo
from experiments.topologies.ring_topo import RingTopo
from experiments.topologies.line_topo import LineTopo

from synthesis.synthesize_dij import SynthesizeDij


class MininetMan():

    def __init__(self,
                 controller_port,
                 topo_name,
                 num_switches,
                 num_hosts_per_switch,
                 experiment_switches):

        self.ping_timeout = 5
        self.num_switches = num_switches
        self.num_hosts_per_switch = num_hosts_per_switch
        self.controller_port = int(controller_port)

        self.experiment_switches = experiment_switches
        self.topo_name = topo_name

        if self.topo_name == "ring":
            self.topo = RingTopo(self.num_switches, self.num_hosts_per_switch)
        elif self.topo_name == "line":
            self.topo = LineTopo(self.num_switches, self.num_hosts_per_switch)
        elif self.topo_name == "two_ring":
            self.topo = TwoRingTopo(self.num_switches, self.num_hosts_per_switch)
        elif self.topo_name == "fat_tree":
            self.topo = FatTree(self.num_switches, self.num_hosts_per_switch)
        else:
            raise Exception("Invalid, unknown topology type: " % topo_name)

    def get_switch_hosts(self, switch_id):

        for i in range(0, self.num_hosts_per_switch):
            host_name = "h" + switch_id[1:] + str(i+1)
            yield self.net.get(host_name)

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

    def setup_mininet(self):

        self.net = Mininet(topo=self.topo,
                           cleanup=True,
                           autoStaticArp=True,
                           controller=lambda name: RemoteController(name, ip='127.0.0.1', port=self.controller_port),
                           switch=OVSSwitch)

        # Start
        self.net.start()

        print "Waiting for the controller to get ready for synthesis"
        time.sleep(200)

        print "Synthesizing..."

        self.ng = NetworkGraph(mininet_man=self)
        self.synthesis_dij = SynthesizeDij(self.ng, master_switch=self.topo_name == "line")
        self.synthesis_dij.synthesize_all_node_pairs()

        print "Synthesis Completed. Waiting for rules to be detected by controller..."
        time.sleep(10*self.topo.total_switches)

        self._ping_experiment_hosts()

    def cleanup_mininet(self):
        print "Mininet cleanup..."
        self.net.stop()
        os.system("sudo mn -c")

    def __del__(self):
        self.cleanup_mininet()