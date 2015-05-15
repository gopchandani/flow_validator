__author__ = 'Rakesh Kumar'

import argparse
import time

from netaddr import IPNetwork

from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.node import OVSSwitch

from fat_tree import FatTree
from two_ring_topo import TwoRingTopo
from ring_topo import RingTopo
from line_topo import LineTopo

from model.match import Match
from synthesis.synthensize_dij import SynthesizeDij
from analysis.backup_paths import BackupPaths
import os

class FlowValidatorTest():

    def __init__(self, topo, num_switches, num_hosts_per_switch, verbose):

        self.ping_interval = 3
        self.num_switches = num_switches
        self.num_hosts_per_switch = num_hosts_per_switch
        self.verbose = verbose
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

        self._start_test()

    def _get_per_link_failure_ping_output(self, src, dst):

        can_ping = False

        # Go over all the links between switches in the topology
        for n1, n2 in self.topo.links():

            if n1.startswith("h") or n2.startswith("h"):
                continue

            print "Checking the impact of link between", n1, n2

            # Bring the link down
            self.net.configLinkStatus(n1, n2, "down")

            # Try ping between the specified hosts
            can_ping = self._ping_host_pair(src, dst)

            # Bring the link back up
            self.net.configLinkStatus(n1, n2, "up")

            if not can_ping:
                break

        return can_ping

    def _get_analysis_output(self, src, dst):

        bp = BackupPaths()

        flow_match = Match()
        flow_match.ethernet_source = bp.model.graph.node[bp.model.get_host_id_node_with_ip(src.IP())]["h"].mac_addr
        flow_match.ethernet_destination = bp.model.graph.node[bp.model.get_host_id_node_with_ip(dst.IP())]["h"].mac_addr
        flow_match.src_ip_addr = IPNetwork(src.IP())
        flow_match.dst_ip_addr = IPNetwork(dst.IP())
        flow_match.ethernet_type = 0x0800
        flow_match.has_vlan_tag = False
        has_bp_flow_1 = bp.has_primary_and_backup(bp.model.get_host_id_node_with_ip(src.IP()),
                                                  bp.model.get_host_id_node_with_ip(dst.IP()),
                                                  flow_match)

        flow_match.ethernet_source = bp.model.graph.node[bp.model.get_host_id_node_with_ip(dst.IP())]["h"].mac_addr
        flow_match.ethernet_destination = bp.model.graph.node[bp.model.get_host_id_node_with_ip(src.IP())]["h"].mac_addr
        flow_match.src_ip_addr = IPNetwork(dst.IP())
        flow_match.dst_ip_addr = IPNetwork(src.IP())
        has_bp_flow_2 = bp.has_primary_and_backup(bp.model.get_host_id_node_with_ip(dst.IP()),
                                                  bp.model.get_host_id_node_with_ip(src.IP()),
                                                  flow_match)

        return has_bp_flow_1 and has_bp_flow_2


    def _compare_ping_and_analysis_output_per_link_failure(self, src, dst):

        can_ping = self._get_per_link_failure_ping_output(src, dst)
        has_backup = self._get_analysis_output(src, dst)

        print "can_ping:", can_ping
        print "has_backup:", has_backup

        return can_ping and has_backup


    def _start_test(self):

        print "Waiting for the controller to boot completely..."
        time.sleep(150)

        #self.net = Mininet(topo=self.topo)
        self.net = Mininet(topo=self.topo,
                           controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6633),
                           switch=OVSSwitch)

        # Start
        self.net.start()


        # Activate Hosts
        self._ping_experiment_hosts()

        time.sleep(60) #reduce?

        print "Synthesizing..."
        # Synthesize rules in the switches
        s = SynthesizeDij()
        s.synthesize_all_node_pairs()
        print "Synthesis Completed."
        time.sleep(60) #reduce?


        for (src, dst) in self._get_experiment_host_pair():

            print "Trying pair, src:", src, "dst:", dst

            checks_out = self._compare_ping_and_analysis_output_per_link_failure(src, dst)
            if checks_out:
                print "The ping results and the analysis output agrees"
            else:
                print "The ping results and the analysis output disagrees."


        time.sleep(60)

        # End
        self.net.stop()

    # Generating for iterating through host-pairs
    def _get_experiment_host_pair(self):

        for src_switch in self.experiment_switches:
            for dst_switch in self.experiment_switches:
                if src_switch == dst_switch:
                    continue

                # Assume that at least one host per switch exists
                src_host = "h" + src_switch[1:] + "1"
                dst_host = "h" + dst_switch[1:] + "1"

                yield (self.net.get(src_host), self.net.get(dst_host))

    def _ping_experiment_hosts(self):
        experiment_host_pairs = self._get_experiment_host_pair()
        for (src_host, dst_host) in experiment_host_pairs:
            self._ping_host_pair(src_host, dst_host)

    def _ping_host_pair(self, src_host, dst_host):
        hosts = [src_host, dst_host]
        ping_loss_rate = self.net.ping(hosts, self.ping_interval)
        print "Ping Loss Rate:", ping_loss_rate

        if ping_loss_rate < 100.0:
            return True
        else:
            return False

def start_controller():
    bashCommand = "sudo docker run -t -i -p=6633:6633 -p=8181:8181 opendaylight /distribution-karaf-0.2.1-Helium-SR1/bin/karaf &"
    os.system(bashCommand)    

def main():

    start_controller()
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