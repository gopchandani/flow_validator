__author__ = 'Rakesh Kumar'

import time
import os
import fcntl
import struct
from socket import *

from functools import partial
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.node import OVSSwitch
from controller_man import ControllerMan
from model.network_graph import NetworkGraph
from model.match import Match

from experiments.topologies.ring_topo import RingTopo
from experiments.topologies.clos_topo import ClosTopo
from mininet.topo import LinearTopo
from experiments.topologies.fat_tree import FatTree
from experiments.topologies.two_ring_topo import TwoRingTopo
from experiments.topologies.ring_line_topo import RingLineTopo
from experiments.topologies.clique_topo import CliqueTopo
from experiments.topologies.ameren_topo import AmerenTopo

from synthesis.dijkstra_synthesis import DijkstraSynthesis
from synthesis.aborescene_synthesis import AboresceneSynthesis
from synthesis.synthesis_lib import SynthesisLib


class NetworkConfiguration(object):

    def __init__(self, controller, 
                 topo_name, topo_params, 
                 load_config, save_config, conf_root, 
                 synthesis_name, synthesis_params):

        self.controller = controller
        self.controller_port = 6633
        self.topo_name = topo_name
        self.topo_params = topo_params
        self.topo_name = topo_name
        self.load_config = load_config
        self.save_config = save_config
        self.conf_root = conf_root
        self.synthesis_name = synthesis_name
        self.synthesis_params = synthesis_params
    
        self.topo = None
        self.nc_topo_str = None
        self.init_topo()
        self.init_synthesis()

        self.mininet_obj = None
        self.cm = None
        self.ng = None

        self.conf_path = self.conf_root + str(self) + "/"
        if not os.path.exists(self.conf_path):
            os.makedirs(self.conf_path)    

    def __str__(self):
        return self.controller + "_" + str(self.synthesis) + "_" + str(self.topo)

    def __del__(self):
        del self.cm
        self.cleanup_mininet()

    def init_topo(self):
        if self.topo_name == "ring":
            self.topo = RingTopo(self.topo_params)
            self.nc_topo_str = "Ring topology with " + str(self.topo.total_switches) + " switches"
        elif self.topo_name == "clostopo":
            self.topo = ClosTopo(self.topo_params)
            self.nc_topo_str = "Ring topology with " + str(self.topo.total_switches) + " switches"
        else:
            raise NotImplemented("Unknown topology type: " % self.topo_name)
            
    def init_synthesis(self):
        if self.synthesis_name == "DijkstraSynthesis":
            self.synthesis_params["master_switch"] = self.topo_name == "linear"
            self.synthesis = DijkstraSynthesis(self.ng.config_path_prefix, self.synthesis_params)

        elif self.synthesis_name == "AboresceneSynthesis":
            self.synthesis = AboresceneSynthesis(self.synthesis_params)

    def trigger_synthesis(self):
        if self.synthesis_name == "DijkstraSynthesis":
            self.synthesis.network_graph = self.ng
            self.synthesis.synthesis_lib = SynthesisLib("localhost", "8181", self.ng)
            self.synthesis.synthesize_all_node_pairs()

        elif self.synthesis_name == "AboresceneSynthesis":
            self.synthesis.network_graph = self.ng
            self.synthesis.synthesis_lib = SynthesisLib("localhost", "8181", self.ng)
            flow_match = Match(is_wildcard=True)
            flow_match["ethernet_type"] = 0x0800
            self.synthesis.synthesize_all_switches(flow_match, 2)

        # self.mininet_obj.pingAll()

        is_bi_connected = self.is_bi_connected_manual_ping_test_all_hosts()

        # is_bi_connected = self.is_bi_connected_manual_ping_test([(self.mininet_obj.get('h11'), self.mininet_obj.get('h31'))])

        # is_bi_connected = self.is_bi_connected_manual_ping_test([(self.mininet_obj.get('h31'), self.mininet_obj.get('h41'))],
        #                                                            [('s1', 's2')])
        # print "is_bi_connected:", is_bi_connected

    def setup_network_graph(self,
                            mininet_setup_gap=None,
                            synthesis_setup_gap=None):

        if not self.load_config and self.save_config:
            self.cm = ControllerMan(controller=self.controller)
            self.controller_port = self.cm.get_next()
            self.start_mininet()
            if mininet_setup_gap:
                time.sleep(mininet_setup_gap)

        # Get a flow validator instance
        self.ng = NetworkGraph(network_configuration=self)

        if not self.load_config and self.save_config:
            self.trigger_synthesis()
            if synthesis_setup_gap:
                time.sleep(synthesis_setup_gap)
        
        # Refresh the network_graph
        self.ng.parse_switches()

        print "total_flow_rules:", self.ng.total_flow_rules

        return self.ng

    def start_mininet(self):

        self.cleanup_mininet()

        self.mininet_obj = Mininet(topo=self.topo,
                           cleanup=True,
                           autoStaticArp=True,
                           controller=lambda name: RemoteController(name, ip='127.0.0.1', port=self.controller_port),
                           switch=partial(OVSSwitch, protocols='OpenFlow14'))

        self.mininet_obj.start()

    def cleanup_mininet(self):

        if self.mininet_obj:
            print "Mininet cleanup..."
            self.mininet_obj.stop()

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
                    yield self.mininet_obj.get(dst_node)

    def _get_experiment_host_pair(self):

        for src_switch in self.topo.get_switches_with_hosts():
            for dst_switch in self.topo.get_switches_with_hosts():
                if src_switch == dst_switch:
                    continue

                # Assume one host per switch
                src_host = "h" + src_switch[1:] + "1"
                dst_host = "h" + dst_switch[1:] + "1"

                src_host_node = self.mininet_obj.get(src_host)
                dst_host_node = self.mininet_obj.get(dst_host)

                yield (src_host_node, dst_host_node)

    def is_host_pair_pingable(self, src_host, dst_host):
        hosts = [src_host, dst_host]
        ping_loss_rate = self.mininet_obj.ping(hosts, '1')

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
        ping_loss_rate = self.mininet_obj.pingAll('1')

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

        for link in self.mininet_obj.links:
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

                self.mininet_obj.configLinkStatus(edge[0], edge[1], 'down')
                self.wait_until_link_status(edge[0], edge[1], 'down')
                time.sleep(5)
                is_pingable_after_failure = self.is_host_pair_pingable(src_host, dst_host)
                self.mininet_obj.configLinkStatus(edge[0], edge[1], 'up')
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

            self.mininet_obj.configLinkStatus(edge[0], edge[1], 'down')
            self.wait_until_link_status(edge[0], edge[1], 'down')
            time.sleep(5)
            is_pingable_after_failure = self.are_all_hosts_pingable()
            self.mininet_obj.configLinkStatus(edge[0], edge[1], 'up')
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
