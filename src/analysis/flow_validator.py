__author__ = 'Rakesh Kumar'

import sys
sys.path.append("./")

import pdb

from memory_profiler import profile
from guppy import hpy

from experiments.controller_man import ControllerMan
from experiments.mininet_man import MininetMan

from model.network_graph import NetworkGraph
from model.port_graph import PortGraph
from model.traffic import Traffic

class FlowValidator:

    def __init__(self, network_graph):
        self.network_graph = network_graph
        self.port_graph = PortGraph(network_graph)

    #@profile
    def init_port_graph(self):
        self.port_graph.init_port_graph()

    #@profile
    def de_init_port_graph(self):
        self.port_graph.de_init_port_graph()

    #@profile
    def add_hosts(self):

        # Attach a destination port for each host.
        for host_id in self.network_graph.get_host_ids():

            host_obj = self.network_graph.get_node_object(host_id)

            self.port_graph.add_port(host_obj.ingress_port)
            self.port_graph.add_port(host_obj.egress_port)

            self.port_graph.add_node_graph_edge(host_id, host_obj.switch_id)

            admitted_traffic = Traffic(init_wildcard=True)
            admitted_traffic.set_field("ethernet_type", 0x0800)
            dst_mac_int = int(host_obj.mac_addr.replace(":", ""), 16)
            admitted_traffic.set_field("ethernet_destination", dst_mac_int)

            admitted_traffic.set_port(host_obj.ingress_port)

            host_obj.ingress_port.admitted_traffic[host_obj.ingress_port.port_id] = admitted_traffic

    #@profile
    def remove_hosts(self):

        for host_id in self.network_graph.get_host_ids():

            host_obj = self.network_graph.get_node_object(host_id)
            self.network_graph.simulate_remove_edge(host_id, host_obj.switch_id)
            self.port_graph.remove_node_graph_edge(host_id, host_obj.switch_id)

    #@profile
    def initialize_admitted_traffic(self):

        for host_id in self.network_graph.get_host_ids():
            host_obj = self.network_graph.get_node_object(host_id)

            if host_id == "h21":
                pass

            #print "Computing admitted_traffic:", host_id, "connected to switch:", \
            #    host_obj.switch_id, "at port:", \
            #    host_obj.switch_port_attached

            switch_egress_port = self.port_graph.get_port(self.port_graph.g.predecessors(host_obj.ingress_port.port_id)[0])

            self.port_graph.compute_admitted_traffic(switch_egress_port,
                                                   host_obj.ingress_port.admitted_traffic[host_obj.ingress_port.port_id],
                                                   host_obj.ingress_port)

    def validate_all_host_pair_basic_reachability(self):

        # Test connectivity after flows have bled through the port graph
        for src_h_id in self.network_graph.get_host_ids():
            for dst_h_id in self.network_graph.get_host_ids():

                src_host_obj = self.network_graph.get_node_object(src_h_id)
                dst_host_obj = self.network_graph.get_node_object(dst_h_id)

                if src_h_id != dst_h_id:

                    if dst_host_obj.ingress_port.port_id not in src_host_obj.egress_port.admitted_traffic:
                        print "No Port Paths from:", src_h_id, "to:", dst_h_id
                        continue

                    at = src_host_obj.egress_port.admitted_traffic[dst_host_obj.ingress_port.port_id]

                    # Baseline
                    at.print_port_paths()

    def validate_all_host_pair_backup_reachability(self, primary_path_edge_dict):

        for host_pair in primary_path_edge_dict:

            src_host_obj = self.network_graph.get_node_object(host_pair[0])
            dst_host_obj = self.network_graph.get_node_object(host_pair[1])

            at = src_host_obj.egress_port.admitted_traffic[dst_host_obj.ingress_port.port_id]

            # Baseline
            baseline_num_elements = len(at.match_elements)

            # Now break the edges in the primary path in this host-pair, one-by-one
            for primary_edge in primary_path_edge_dict[host_pair]:

                self.network_graph.simulate_remove_edge(primary_edge[0], primary_edge[1])
                self.port_graph.remove_node_graph_edge(primary_edge[0], primary_edge[1])
                at = src_host_obj.egress_port.admitted_traffic[dst_host_obj.ingress_port.port_id]

                edge_removed_num_elements = len(at.match_elements)

                # Add it back
                self.network_graph.simulate_add_edge(primary_edge[0], primary_edge[1])
                self.port_graph.add_node_graph_edge(primary_edge[0], primary_edge[1], True)
                at = src_host_obj.egress_port.admitted_traffic[dst_host_obj.ingress_port.port_id]
                edge_added_back_num_elements = len(at.match_elements)

                # the number of elements should be same in three scenarios for each edge
                if not(baseline_num_elements == edge_removed_num_elements == edge_added_back_num_elements):
                    print "Backup doesn't quite exist between pair:", host_pair, "due to edge:", primary_edge
                    return

def main():

    # Get a controller
    cm = ControllerMan(1)
    controller_port = cm.get_next()

    # Get a mininet instance
    mm = MininetMan(controller_port, "line", 2, 1, experiment_switches=["s1", "s2"])
    mm.setup_mininet()

    # Get a flow validator instance
    ng = NetworkGraph(mininet_man=mm)
    fv = FlowValidator(ng)

#    hp = hpy()
#    before = hp.heap()

    # Three steps to happy living:
    fv.init_port_graph()
    fv.add_hosts()
    fv.initialize_admitted_traffic()
    #
    fv.validate_all_host_pair_basic_reachability()
    # fv.remove_hosts()
    # fv.validate_all_host_pair_basic_reachability()

    fv.de_init_port_graph()

#    after = hp.heap()
#    leftover = after - before

#    print leftover
#    pdb.set_trace()

if __name__ == "__main__":
    main()
