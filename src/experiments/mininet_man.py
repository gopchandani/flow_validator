__author__ = 'Rakesh Kumar'


import json
import time
import os
import httplib2

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
from synthesis.synthesize_dij_qos import SynthesizeQoS
from synthesis.intent_synthesis import IntentSynthesis


class MininetMan():

    def __init__(self,
                controller_port,
                controller_host,
                topo_name,
                num_switches,
                num_hosts_per_switch):

        self.net = None
        self.ping_timeout = 5
        self.num_switches = num_switches
        self.num_hosts_per_switch = num_hosts_per_switch
        self.controller_port = int(controller_port)
        if controller_host:
            self.controller_host = controller_host
        else:
            self.controller_host = "127.0.0.1"

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
                           controller=lambda name: RemoteController(name, ip=self.controller_host, port=self.controller_port),
                           switch=self.switch)

        self.net.start()


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

    def setup_mininet_with_odl(self, ng):

        print "Synthesizing..."

        self.synthesis = IntentSynthesis(ng, master_switch=self.topo_name == "linear")
        self.synthesis.synthesize_all_node_pairs()

        print "Synthesis Completed. Waiting for rules to be detected by controller..."
        time.sleep(30 * self.num_hosts_per_switch * self.num_switches)

        self.net.pingAll(self.ping_timeout)

    def setup_mininet_with_sel(self, ng):
        print("Synthesizing....")

        self.synthesis = IntentSynthesis(ng, master_switch=self.topo_name == "linear")
        self.synthesis.synthesize_all_node_pairs()

        #print("Synthesis Completed. Waiting for rules to be detected by controller...")
        # time.sleep(30 * self.num_hosts_per_switch * self.num_switches)

        # self.net.pingAll(self.ping_timeout)

    def setup_mininet_with_ryu(self, ng):

        print "Synthesizing..."

        self.synthesis = IntentSynthesis(ng, master_switch=self.topo_name == "linear")
        self.synthesis.synthesize_all_node_pairs()

        # self.s1 = self.net.getNodeByName("s1")
        # self.s1.addIntf("s1-eth5", self.s1.newPort())

        self.net.pingAll(self.ping_timeout)
        #
        # self.h11 = self.net.getNodeByName("h11")
        # self.h31 = self.net.getNodeByName("h31")
        #
        # # Ping from h1-> h3
        # print self.h11.cmd("ping -c3 " + self.h31.IP())


    def setup_mininet_with_ryu_qos(self, ng):

        self.synthesis_dij = SynthesizeQoS(ng, master_switch=self.topo_name == "linear")
        self.synthesis_dij.synthesize_all_node_pairs(10)

        # Get all the nodes
        self.h1s1 = self.net.getNodeByName("h1s1")
        self.h1s2 = self.net.getNodeByName("h1s2")
        self.h2s1 = self.net.getNodeByName("h2s1")
        self.h2s2 = self.net.getNodeByName("h2s2")

        # Start the server at h1s1
        h1s1_output = self.h1s1.cmd("iperf -s -u -i 1 5001&")
        print h1s1_output

        # Start the client at h1s2
        h1s2_output = self.h1s2.cmd("iperf -c " + self.h1s1.IP() + " -p 5001 -u -b 3M -t 1")
        print h1s2_output
        time.sleep(1)

        h1s2_output = self.h1s2.cmd("iperf -c " + self.h1s1.IP() + " -p 5001 -u -b 6M -t 1")
        print h1s2_output
        time.sleep(1)

        h1s2_output = self.h1s2.cmd("iperf -c " + self.h1s1.IP() + " -p 5001 -u -b 9M -t 1")
        print h1s2_output
        time.sleep(1)

        h1s2_output = self.h1s2.cmd("iperf -c " + self.h1s1.IP() + " -p 5001 -u -b 12M -t 1")
        print h1s2_output
        time.sleep(1)

        h1s2_output = self.h1s2.cmd("iperf -c " + self.h1s1.IP() + " -p 5001 -u -b 15M -t 1")
        print h1s2_output
        time.sleep(1)


    def setup_mininet_with_ryu_router(self):

        # Get all the nodes
        self.h1 = self.net.getNodeByName("h1")
        self.h2 = self.net.getNodeByName("h2")
        self.h3 = self.net.getNodeByName("h3")

        self.h1.cmd("ip addr del 10.0.0.1/8 dev h1-eth0")
        self.h1.cmd("ip addr add 172.16.20.10/24 dev h1-eth0")
        self.h1.cmd("ip route add default via 172.16.20.1")

        self.h2.cmd("ip addr del 10.0.0.2/8 dev h2-eth0")
        self.h2.cmd("ip addr add 172.16.10.10/24 dev h2-eth0")
        self.h2.cmd("ip route add default via 172.16.10.1")

        self.h3.cmd("ip addr del 10.0.0.3/8 dev h3-eth0")
        self.h3.cmd("ip addr add 192.168.30.10/24 dev h3-eth0")
        self.h3.cmd("ip route add default via 192.168.30.1")

        self.h = httplib2.Http(".cache")
        self.baseUrl = "http://localhost:8080"

        router_conf_requests = []
        router_conf_requests.append(({"address": "172.16.20.1/24"},
                                     "/router/0000000000000001"))
        router_conf_requests.append(({"address": "172.16.30.30/24"},
                                     "/router/0000000000000001"))
        router_conf_requests.append(({"gateway": "172.16.30.1"},
                                     "/router/0000000000000001"))

        router_conf_requests.append(({"address": "172.16.10.1/24"},
                                     "/router/0000000000000002"))
        router_conf_requests.append(({"address": "172.16.30.1/24"},
                                     "/router/0000000000000002"))
        router_conf_requests.append(({"address": "192.168.10.1/24"},
                                     "/router/0000000000000002"))
        router_conf_requests.append(({"gateway": "172.16.30.30"},
                                     "/router/0000000000000002"))
        router_conf_requests.append(({"destination": "192.168.30.0/24", "gateway": "192.168.10.20"},
                                     "/router/0000000000000002"))


        router_conf_requests.append(({"address": "192.168.30.1/24"},
                                     "/router/0000000000000003"))
        router_conf_requests.append(({"address": "192.168.10.20/24"},
                                     "/router/0000000000000003"))
        router_conf_requests.append(({"gateway": "192.168.10.1"},
                                     "/router/0000000000000003"))


        for data, remainingUrl in router_conf_requests:

            resp, content = self.h.request(uri=self.baseUrl + remainingUrl,
                                           method="POST",
                                           headers={'Content-Type': 'application/json; charset=UTF-8'},
                                           body=json.dumps(data))

            time.sleep(0.2)

            if resp["status"] != "200":
                print "Problem Resp:", resp

        # Ping from h1-> h3
        print self.h1.cmd("ping -c3 192.168.30.10")

        # Ping from h2->h3
        print self.h2.cmd("ping -c3 192.168.30.10")

        # Ping from h2->h1
        print self.h2.cmd("ping -c3 172.16.20.10")

    def cleanup(self):

        if self.net:
            print "Mininet cleanup..."
            self.net.stop()
            os.system("sudo mn -c")

    def __del__(self):
        self.cleanup()

def main():

    topo_description = ("linear", 3, 1)
    mm = MininetMan(6633, *topo_description)
    mm.setup_mininet_with_ryu_router()

if __name__ == "__main__":
    main()