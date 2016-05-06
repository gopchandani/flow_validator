__author__ = 'Rakesh Kumar'


import json
import time
import os
import httplib2
import fcntl, struct
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

from synthesis.synthesize_dij_qos import SynthesizeQoS


class MininetMan():

    def __init__(self,
                 synthesis_scheme,
                 controller_port,
                 topo_name,
                 num_switches,
                 num_hosts_per_switch,
                 fanout=None,
                 core=None,
                 per_switch_links=None,
                 dst_ports_to_synthesize=''):

        self.net = None
        self.synthesis_scheme = synthesis_scheme

        self.num_switches = num_switches
        self.num_hosts_per_switch = num_hosts_per_switch
        self.fanout = fanout
        self.core = core
        self.controller_port = int(controller_port)

        self.topo_name = topo_name
        self.experiment_switches = None

        if self.topo_name == "ring":
            self.topo = RingTopo(self.num_switches, self.num_hosts_per_switch)
            self.experiment_switches = self.topo.switch_names
        elif self.topo_name == "linear":
            self.topo = LinearTopo(self.num_switches, self.num_hosts_per_switch)
        elif self.topo_name == "two_ring":
            self.topo = TwoRingTopo(self.num_switches, self.num_hosts_per_switch)
        elif self.topo_name == "fat_tree":
            self.topo = FatTree(self.num_switches, self.num_hosts_per_switch)
        elif self.topo_name == "ringline":
            self.topo = RingLineTopo(self.num_switches, self.num_hosts_per_switch)
        elif self.topo_name == "clostopo":
            self.topo = ClosTopo(self.fanout, self.core, self.num_hosts_per_switch)
            self.experiment_switches = self.topo.edge_switches.values()
        elif self.topo_name == "cliquetopo":
            self.topo = CliqueTopo(self.num_switches, self.num_hosts_per_switch, per_switch_links)
        elif self.topo_name == "amerentopo":
            self.topo = AmerenTopo()
        else:
            raise Exception("Invalid, unknown topology type: " % topo_name)

        self.switch = partial(OVSSwitch, protocols='OpenFlow13')

        if self.num_switches and self.num_hosts_per_switch:
            self.mininet_configuration_name = self.synthesis_scheme + "_" + \
                                              self.topo_name + "_" + \
                                              str(self.num_switches) + "_" + \
                                              str(self.num_hosts_per_switch) + \
                                              "_" + str(dst_ports_to_synthesize)

        elif self.fanout and self.core and self.num_hosts_per_switch:
            self.mininet_configuration_name = self.synthesis_scheme + "_" + \
                                              self.topo_name + "_" + \
                                              str(self.num_hosts_per_switch) + "_" + \
                                              str(self.fanout) + "_" + \
                                              str(self.core) + "_" \
                                              + str(dst_ports_to_synthesize)
        else:
            self.mininet_configuration_name = self.synthesis_scheme + "_" + \
                                              self.topo_name + "_" \
                                              + str(dst_ports_to_synthesize)

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

    def get_experiment_switch_hosts(self, switch_id, experiment_switches):

        if switch_id in experiment_switches:
            for i in xrange(0, self.num_hosts_per_switch):
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

    def is_bi_connected_manual_ping_test(self, experiment_host_pairs_to_check=None, edges_to_try=None):

        is_bi_connected= True

        if not edges_to_try:
            edges_to_try = self.topo.g.edges()

        for edge in edges_to_try:

            # Only try and break switch-switch edges
            if edge[0].startswith("h") or edge[1].startswith("h"):
                continue

            if not experiment_host_pairs_to_check:
                experiment_host_pairs_to_check = list(self._get_experiment_host_pair())

            for (src_host, dst_host) in experiment_host_pairs_to_check:

                #is_pingable_before_failure = self.is_host_pair_pingable(src_host, dst_host)

                # if not is_pingable_before_failure:
                #     print "src_host:", src_host, "dst_host:", dst_host, "are not connected."
                #     is_bi_connected = False
                #     break

                self.net.configLinkStatus(edge[0], edge[1], 'down')
                self.wait_until_link_status(edge[0], edge[1], 'down')
                time.sleep(5)
                is_pingable_after_failure = self.is_host_pair_pingable(src_host, dst_host)
                self.net.configLinkStatus(edge[0], edge[1], 'up')
                self.wait_until_link_status(edge[0], edge[1], 'up')

                time.sleep(5)
                # is_pingable_after_restoration = self.is_host_pair_pingable(src_host, dst_host)
                #
                # if not is_pingable_after_failure == True:
                #     is_bi_connected = False
                #     print "Got a problem with edge:", edge, " for src_host:", src_host, "dst_host:", dst_host
                #     break

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

    def parse_netperf_output(self,netperf_output_string):
        data_lines =  netperf_output_string.split('\r\n')

        output_line_tokens =  data_lines[2].split(',')
        print "Throughput:", output_line_tokens[0]
        print 'Mean Latency:', output_line_tokens[1]
        print 'Stddev Latency:', output_line_tokens[2]
        print '99th Latency:', output_line_tokens[3]
        print 'Min Latency:', output_line_tokens[4]
        print 'Max Latency:', output_line_tokens[5]


    def qos_setup_single_flow_test(self, ng):

        self.synthesis_dij = SynthesizeQoS(ng)
        last_hop_queue_rate = 50
        self.synthesis_dij.synthesize_all_node_pairs(last_hop_queue_rate)

        num_traffic_profiles = 10
        size_of_send = [1024, 1024, 1024, 1024, 1024, 1024, 1024, 1024, 1024, 1024]
        # number_of_sends_in_a_burst = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        # inter_burst_times = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10]

        number_of_sends_in_a_burst = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        inter_burst_times = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

        # Get all the nodes
        self.h1s1 = self.net.getNodeByName("h1s1")
        self.h1s2 = self.net.getNodeByName("h1s2")
        self.h2s1 = self.net.getNodeByName("h2s1")
        self.h2s2 = self.net.getNodeByName("h2s2")

        h1s1_output = self.h1s1.cmd("/usr/local/bin/netserver")
        print h1s1_output

        netperf_output_dict = {}

        for i in range(num_traffic_profiles):

            netperf_output_dict[i] = self.h1s2.cmd("/usr/local/bin/netperf -H " + self.h1s1.IP() +
                                                   " -w " + str(inter_burst_times[i]) +
                                                   " -b " + str(number_of_sends_in_a_burst[i]) +
                                                   " -l 10 " +
                                                   "-t omni -- -d send -o " +
                                                   "'THROUGHPUT, MEAN_LATENCY, STDDEV_LATENCY, P99_LATENCY, MIN_LATENCY, MAX_LATENCY'" +
                                                   " -T UDP_RR " +
                                                   "-m " + str(size_of_send[i])
                                                   )
            print netperf_output_dict[i]

        # Parse the output for jitter and delay
        print "Last-Hop Queue Rate:", str(last_hop_queue_rate), "M"
        for i in range(num_traffic_profiles):

            print "--"
            print "Size of send (bytes):", size_of_send[i]
            print "Number of sends in a burst:", number_of_sends_in_a_burst[i]
            print "Inter-burst time (miliseconds):", inter_burst_times[i]

            rate = (size_of_send[i] * 8 * number_of_sends_in_a_burst[i]) / (inter_burst_times[i] * 1000.0)
            print "Sending Rate:", str(rate), 'Mbps'

            self.parse_netperf_output(netperf_output_dict[i])

    def qos_setup_two_flows_on_separate_queues_to_two_different_hosts(self, ng, same_output_queue=False):

        self.synthesis_dij = SynthesizeQoS(ng, same_output_queue=same_output_queue)
        last_hop_queue_rate = 50
        self.synthesis_dij.synthesize_all_node_pairs(last_hop_queue_rate)

        num_traffic_profiles = 10
        size_of_send = [1024, 1024, 1024, 1024, 1024, 1024, 1024, 1024, 1024, 1024]

        number_of_sends_in_a_burst = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        inter_burst_times = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

        # Get all the nodes
        self.h1s1 = self.net.getNodeByName("h1s1")
        self.h1s2 = self.net.getNodeByName("h1s2")
        self.h2s1 = self.net.getNodeByName("h2s1")
        self.h2s2 = self.net.getNodeByName("h2s2")

        h1s1_output = self.h1s1.cmd("/usr/local/bin/netserver")
        print h1s1_output

        h2s1_output = self.h2s1.cmd("/usr/local/bin/netserver")
        print h2s1_output

        netperf_output_dict_h1s2 = {}
        netperf_output_dict_h2s2 = {}

        for i in range(num_traffic_profiles):

            netperf_output_dict_h1s2[i] = self.h1s2.cmd("/usr/local/bin/netperf -H " + self.h1s1.IP() +
                                                   " -w " + str(inter_burst_times[i]) +
                                                   " -b " + str(number_of_sends_in_a_burst[i]) +
                                                   " -l 10 " +
                                                   "-t omni -- -d send -o " +
                                                   "'THROUGHPUT, MEAN_LATENCY, STDDEV_LATENCY, P99_LATENCY, MIN_LATENCY, MAX_LATENCY'" +
                                                   " -T UDP_RR " +
                                                   "-m " + str(size_of_send[i]) + " &"
                                                   )

            netperf_output_dict_h2s2[i] = self.h2s2.cmd("/usr/local/bin/netperf -H " + self.h2s1.IP() +
                                                   " -w " + str(inter_burst_times[i]) +
                                                   " -b " + str(number_of_sends_in_a_burst[i]) +
                                                   " -l 10 " +
                                                   "-t omni -- -d send -o " +
                                                   "'THROUGHPUT, MEAN_LATENCY, STDDEV_LATENCY, P99_LATENCY, MIN_LATENCY, MAX_LATENCY'" +
                                                   " -T UDP_RR " +
                                                   "-m " + str(size_of_send[i]) + " &"
                                                   )
            time.sleep(15)

            netperf_output_dict_h1s2[i] = self.h1s2.read()
            netperf_output_dict_h2s2[i] = self.h2s2.read()

            print netperf_output_dict_h1s2[i]
            print netperf_output_dict_h2s2[i]

        # Parse the output for jitter and delay
        print "Last-Hop Queue Rate:", str(last_hop_queue_rate), "M"
        for i in range(num_traffic_profiles):

            print "--"
            print "Size of send (bytes):", size_of_send[i]
            print "Number of sends in a burst:", number_of_sends_in_a_burst[i]
            print "Inter-burst time (miliseconds):", inter_burst_times[i]

            rate = (size_of_send[i] * 8 * number_of_sends_in_a_burst[i]) / (inter_burst_times[i] * 1000.0)
            print "Sending Rate:", str(rate), 'Mbps'

            self.parse_netperf_output(netperf_output_dict_h1s2[i])
            print "--"
            self.parse_netperf_output(netperf_output_dict_h2s2[i])

    def qos_setup_two_flows_on_separate_queues_to_same_host(self, ng, same_output_queue=False):

        self.synthesis_dij = SynthesizeQoS(ng, same_output_queue=same_output_queue)
        last_hop_queue_rate = 50
        self.synthesis_dij.synthesize_all_node_pairs(last_hop_queue_rate)

        num_traffic_profiles = 10
        size_of_send = [1024, 1024, 1024, 1024, 1024, 1024, 1024, 1024, 1024, 1024]

        number_of_sends_in_a_burst = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        inter_burst_times = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

        # Get all the nodes
        self.h1s1 = self.net.getNodeByName("h1s1")
        self.h1s2 = self.net.getNodeByName("h1s2")
        self.h2s1 = self.net.getNodeByName("h2s1")
        self.h2s2 = self.net.getNodeByName("h2s2")

        h1s1_output = self.h1s1.cmd("/usr/local/bin/netserver")
        print h1s1_output

        h2s1_output = self.h2s1.cmd("/usr/local/bin/netserver")
        print h2s1_output

        netperf_output_dict_h1s2 = {}
        netperf_output_dict_h2s2 = {}

        for i in range(num_traffic_profiles):

            netperf_output_dict_h1s2[i] = self.h1s2.cmd("/usr/local/bin/netperf -H " + self.h2s1.IP() +
                                                   " -w " + str(inter_burst_times[i]) +
                                                   " -b " + str(number_of_sends_in_a_burst[i]) +
                                                   " -l 10 " +
                                                   "-t omni -- -d send -o " +
                                                   "'THROUGHPUT, MEAN_LATENCY, STDDEV_LATENCY, P99_LATENCY, MIN_LATENCY, MAX_LATENCY'" +
                                                   " -T UDP_RR " +
                                                   "-m " + str(size_of_send[i]) + " &"
                                                   )

            netperf_output_dict_h2s2[i] = self.h2s2.cmd("/usr/local/bin/netperf -H " + self.h2s1.IP() +
                                                   " -w " + str(inter_burst_times[i]) +
                                                   " -b " + str(number_of_sends_in_a_burst[i]) +
                                                   " -l 10 " +
                                                   "-t omni -- -d send -o " +
                                                   "'THROUGHPUT, MEAN_LATENCY, STDDEV_LATENCY, P99_LATENCY, MIN_LATENCY, MAX_LATENCY'" +
                                                   " -T UDP_RR " +
                                                   "-m " + str(size_of_send[i]) + " &"
                                                   )
            time.sleep(15)

            netperf_output_dict_h1s2[i] = self.h1s2.read()
            netperf_output_dict_h2s2[i] = self.h2s2.read()

            print netperf_output_dict_h1s2[i]
            print netperf_output_dict_h2s2[i]

        # Parse the output for jitter and delay
        print "Last-Hop Queue Rate:", str(last_hop_queue_rate), "M"
        for i in range(num_traffic_profiles):

            print "--"
            print "Size of send (bytes):", size_of_send[i]
            print "Number of sends in a burst:", number_of_sends_in_a_burst[i]
            print "Inter-burst time (miliseconds):", inter_burst_times[i]

            rate = (size_of_send[i] * 8 * number_of_sends_in_a_burst[i]) / (inter_burst_times[i] * 1000.0)
            print "Sending Rate:", str(rate), 'Mbps'

            self.parse_netperf_output(netperf_output_dict_h1s2[i])
            print "--"
            self.parse_netperf_output(netperf_output_dict_h2s2[i])