__author__ = 'Rakesh Kumar'

import time
import os
import fcntl
import struct
from socket import *

from functools import partial

from mininet.topo import LinearTopo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.node import OVSSwitch

from experiments.topologies.fat_tree import FatTree
from experiments.topologies.two_ring_topo import TwoRingTopo
from experiments.topologies.ring_topo import RingTopo
from experiments.topologies.ring_line_topo import RingLineTopo
from experiments.topologies.clos_topo import ClosTopo
from experiments.topologies.clique_topo import CliqueTopo
from experiments.topologies.ameren_topo import AmerenTopo


class NetworkConfiguration(object):

    def __init__(self, controller, topo_name, topo_params, load_config, save_config, synthesis_scheme):

        self.controller = controller
        self.controller_port = 6633
        self.topo_name = topo_name
        self.topo_params = topo_params
        self.topo_name = topo_name
        self.load_config = load_config
        self.save_config = save_config
        self.synthesis_scheme = synthesis_scheme

        if self.topo_name == "ring":
            self.topo = RingTopo(**topo_params)
        elif self.topo_name == "clostopo":
            self.topo = ClosTopo(**topo_params)
        elif self.topo_name == "linear":
            self.topo = LinearTopo(**topo_params)
        elif self.topo_name == "two_ring":
            self.topo = TwoRingTopo(**topo_params)
        elif self.topo_name == "fat_tree":
            self.topo = FatTree(**topo_params)
        elif self.topo_name == "ringline":
            self.topo = RingLineTopo(**topo_params)
        elif self.topo_name == "cliquetopo":
            self.topo = CliqueTopo(**topo_params)
        elif self.topo_name == "amerentopo":
            self.topo = AmerenTopo()
        else:
            raise Exception("Invalid, unknown topology type: " % topo_name)

        self.switch = partial(OVSSwitch, protocols='OpenFlow14')
        self.net = None

        self.mininet_configuration_name = self.synthesis_scheme + "_" + str(self.topo)

    def __str__(self):
        if self.topo_name == "ring":
            return "Ring topology with " + str(self.topo.total_switches) + " switches"

        elif self.topo_name == "clostopo":
            return "Clos topology with " + str(self.topo.total_switches) + " switches"

    def __del__(self):
        self.cleanup_mininet()

    def start_mininet(self):

        self.cleanup_mininet()

        self.net = Mininet(topo=self.topo,
                           cleanup=True,
                           autoStaticArp=True,
                           controller=lambda name: RemoteController(name, ip='127.0.0.1', port=self.controller_port),
                           switch=self.switch)

        self.net.start()

    def cleanup_mininet(self):

        if self.net:
            print "Mininet cleanup..."
            self.net.stop()

        os.system("sudo mn -c")

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

    def _get_experiment_host_pair(self):

        for src_switch in self.topo.get_switches_with_hosts():
            for dst_switch in self.topo.get_switches_with_hosts():
                if src_switch == dst_switch:
                    continue

                # Assume one host per switch
                src_host = "h" + src_switch[1:] + "1"
                dst_host = "h" + dst_switch[1:] + "1"

                src_host_node = self.net.get(src_host)
                dst_host_node = self.net.get(dst_host)

                yield (src_host_node, dst_host_node)

    def is_host_pair_pingable(self, src_host, dst_host):
        hosts = [src_host, dst_host]
        ping_loss_rate = self.net.ping(hosts, '1')

        # If some packets get through, then declare pingable
        if ping_loss_rate < 100.0:
            return True
        else:
            # If not, do a double check:
            cmd_output = src_host.cmd("ping -c 3 " + dst_host.IP())
            print cmd_output
            if cmd_output.find("0 received") != -1:
                return False
            else:
                return True

    def are_all_hosts_pingable(self):
        ping_loss_rate = self.net.pingAll('1')

        # If some packets get through, then declare pingable
        if ping_loss_rate < 100.0:
            return True
        else:
            return False

    def get_intf_status(self, ifname):

        # set some symbolic constants
        SIOCGIFFLAGS = 0x8913
        null256 = '\0'*256

        # create a socket so we have a handle to query
        s = socket(AF_INET, SOCK_DGRAM)

        # call ioctl() to get the flags for the given interface
        result = fcntl.ioctl(s.fileno(), SIOCGIFFLAGS, ifname + null256)

        # extract the interface's flags from the return value
        flags, = struct.unpack('H', result[16:18])

        # check "UP" bit and print a message
        up = flags & 1

        return ('down', 'up')[up]

    def wait_until_link_status(self, sw_i, sw_j, intended_status):

        num_seconds = 0

        for link in self.net.links:
            if (sw_i in link.intf1.name and sw_j in link.intf2.name) or (sw_i in link.intf2.name and sw_j in link.intf1.name):

                while True:
                    status_i = self.get_intf_status(link.intf1.name)
                    status_j = self.get_intf_status(link.intf2.name)

                    if status_i == intended_status and status_j == intended_status:
                        break

                    time.sleep(1)
                    num_seconds +=1

        return num_seconds

    def is_bi_connected_manual_ping_test(self, experiment_host_pairs_to_check, edges_to_try=None):

        is_bi_connected= True

        if not edges_to_try:
            edges_to_try = self.topo.g.edges()

        for edge in edges_to_try:

            # Only try and break switch-switch edges
            if edge[0].startswith("h") or edge[1].startswith("h"):
                continue

            for (src_host, dst_host) in experiment_host_pairs_to_check:

                is_pingable_before_failure = self.is_host_pair_pingable(src_host, dst_host)

                if not is_pingable_before_failure:
                    print "src_host:", src_host, "dst_host:", dst_host, "are not connected."
                    is_bi_connected = False
                    break

                self.net.configLinkStatus(edge[0], edge[1], 'down')
                self.wait_until_link_status(edge[0], edge[1], 'down')
                time.sleep(5)
                is_pingable_after_failure = self.is_host_pair_pingable(src_host, dst_host)
                self.net.configLinkStatus(edge[0], edge[1], 'up')
                self.wait_until_link_status(edge[0], edge[1], 'up')

                time.sleep(5)
                is_pingable_after_restoration = self.is_host_pair_pingable(src_host, dst_host)

                if not is_pingable_after_failure == True:
                    is_bi_connected = False
                    print "Got a problem with edge:", edge, " for src_host:", src_host, "dst_host:", dst_host
                    break

        return is_bi_connected

    def is_bi_connected_manual_ping_test_all_hosts(self,  edges_to_try=None):

        is_bi_connected= True

        if not edges_to_try:
            edges_to_try = self.topo.g.edges()

        for edge in edges_to_try:

            # Only try and break switch-switch edges
            if edge[0].startswith("h") or edge[1].startswith("h"):
                continue

            is_pingable_before_failure = self.are_all_hosts_pingable()

            if not is_pingable_before_failure:
                is_bi_connected = False
                break

            self.net.configLinkStatus(edge[0], edge[1], 'down')
            self.wait_until_link_status(edge[0], edge[1], 'down')
            time.sleep(5)
            is_pingable_after_failure = self.are_all_hosts_pingable()
            self.net.configLinkStatus(edge[0], edge[1], 'up')
            self.wait_until_link_status(edge[0], edge[1], 'up')

            time.sleep(5)
            is_pingable_after_restoration = self.are_all_hosts_pingable()

            if not is_pingable_after_failure == True:
                is_bi_connected = False
                break

        return is_bi_connected

    def parse_iperf_output(self, iperf_output_string):
        data_lines =  iperf_output_string.split('\r\n')
        interesting_line_index = None
        for i in xrange(len(data_lines)):
            if data_lines[i].endswith('Server Report:'):
                interesting_line_index = i + 1
        data_tokens =  data_lines[interesting_line_index].split()
        print "Transferred Rate:", data_tokens[7]
        print "Jitter:", data_tokens[9]

    def parse_ping_output(self,ping_output_string):

        data_lines =  ping_output_string.split('\r\n')
        interesting_line_index = None
        for i in xrange(len(data_lines)):
            if data_lines[i].startswith('5 packets transmitted'):
                interesting_line_index = i + 1
        data_tokens =  data_lines[interesting_line_index].split()
        data_tokens =  data_tokens[3].split('/')
        print 'Min Delay:', data_tokens[0]
        print 'Avg Delay:', data_tokens[1]
        print 'Max Delay:', data_tokens[2]
