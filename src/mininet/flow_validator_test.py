__author__ = 'Rakesh Kumar'

import argparse
import time

from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.node import OVSSwitch

from fat_tree import FatTree
from two_ring_topo import TwoRingTopo
from ring_topo import RingTopo
from line_topo import LineTopo

class FlowValidatorTest():

    def __init__(self, topo, num_switches, num_hosts_per_switch, verbose):

        self.num_switches = num_switches
        self.num_hosts_per_switch = num_hosts_per_switch
        self.verbose = verbose

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


        self._start_test()

    def _start_test(self):

        #self.net = Mininet(topo=self.topo)
        self.net = Mininet(topo=self.topo,
                           controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6633),
                           switch=OVSSwitch)

        # Start
        self.net.start()

        time.sleep(10)

        # End
        self.net.stop()

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("-t", "--topo",
                        help="Which topo: ring|line|two_ring|fat_tree",
                        required=True)
    parser.add_argument("-ns", "--num_switches",
                        help="Number of switches (fat_tree: switches on the bottom layer, \
                        two_ring: switches in a single ring, \
                        total number of switches otherwise",
                        type = int,
                        required = True)
    parser.add_argument("-hps", "--num_hosts_per_switch",
                        help="Number of hosts under each switch",
                        type = int,
                        required=True)

    parser.add_argument("-v", "--verbose", action="store_true", help="increase output verbosity")

    args = parser.parse_args()


    fvt = FlowValidatorTest(topo=args.topo,
                            num_switches=args.num_switches,
                            num_hosts_per_switch=args.num_hosts_per_switch,
                            verbose=args.verbose)
if __name__ == "__main__":
    main()