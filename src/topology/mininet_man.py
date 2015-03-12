__author__ = 'Rakesh Kumar'


import time

from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.node import OVSSwitch

from experiments.topologies.fat_tree import FatTree
from experiments.topologies.two_ring_topo import TwoRingTopo
from experiments.topologies.ring_topo import RingTopo
from experiments.topologies.line_topo import LineTopo

from synthesis.synthesize_dij import SynthesizeDij


class MininetMan():

    def __init__(self, controller_port, topo, num_switches, num_hosts_per_switch, verbose=False):

        self.ping_interval = 3
        self.num_switches = num_switches
        self.num_hosts_per_switch = num_hosts_per_switch
        self.verbose = verbose
        self.controller_port = int(controller_port)

        self.experiment_switches = ["s1", "s3"]

        if topo == "ring":
            self.topo = RingTopo(self.num_switches, self.num_hosts_per_switch)
        elif topo == "line":
            self.topo = LineTopo(self.num_switches, self.num_hosts_per_switch)
        elif topo == "two_ring":
            self.topo = TwoRingTopo(self.num_switches, self.num_hosts_per_switch)
        elif topo == "fat_tree":
            self.topo = FatTree(self.num_switches, self.num_hosts_per_switch)
        else:
            raise Exception("Invalid, unknown topology type: " % topo)

    def _get_experiment_host_pair(self):

        for src_switch in self.experiment_switches:
            for dst_switch in self.experiment_switches:
                if src_switch == dst_switch:
                    continue

                # Assume that at least one host per switch exists
                src_host = "h" + src_switch[1:] + "1"
                dst_host = "h" + dst_switch[1:] + "1"

                yield (self.net.get(src_host), self.net.get(dst_host))

    def _ping_host_pair(self, src_host, dst_host):
        hosts = [src_host, dst_host]
        ping_loss_rate = self.net.ping(hosts, self.ping_interval)
        print "Ping Loss Rate:", ping_loss_rate

        if ping_loss_rate < 100.0:
            return True
        else:
            return False

    def _ping_experiment_hosts(self):
        experiment_host_pairs = self._get_experiment_host_pair()
        for (src_host, dst_host) in experiment_host_pairs:
            self._ping_host_pair(src_host, dst_host)

    def setup_mininet(self):

        print "Waiting for the controller to boot completely..."
        #time.sleep(120)

        self.net = Mininet(topo=self.topo,
                           cleanup=True,
                           controller=lambda name: RemoteController(name, ip='127.0.0.1', port=self.controller_port),
                           switch=OVSSwitch)

        # Start
        self.net.start()


        print "Running a ping before synthesis..."
        # Activate Hosts
        self._ping_experiment_hosts()

        print "Waiting for hosts to be detected by controller..."
        #time.sleep(120)

        print "Synthesizing..."

        # Synthesize rules in the switches
        s = SynthesizeDij()
        s.synthesize_all_node_pairs()

        print "Synthesis Completed. Waiting for rules to be detected by controller..."
        #time.sleep(60)

    def __del__(self):
        self.net.stop()
        self.net.cleanup()