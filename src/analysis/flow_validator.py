__author__ = 'Rakesh Kumar'

import sys
import time
sys.path.append("./")

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
        for host_id in self.network_graph.get_experiment_host_ids():

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

        for host_id in self.network_graph.get_experiment_host_ids():
            host_obj = self.network_graph.get_node_object(host_id)
            self.port_graph.remove_node_graph_edge(host_id, host_obj.switch_id)

    #@profile
    def initialize_admitted_traffic(self):

        for host_id in self.network_graph.get_experiment_host_ids():
            host_obj = self.network_graph.get_node_object(host_id)

            #print "Computing admitted_traffic:", host_id, "connected to switch:", \
            #    host_obj.switch_id, "at port:", \
            #    host_obj.switch_port_attached

            switch_egress_port = self.port_graph.get_port(self.port_graph.g.predecessors(host_obj.ingress_port.port_id)[0])

            self.port_graph.compute_admitted_traffic(switch_egress_port,
                                                   host_obj.ingress_port.admitted_traffic[host_obj.ingress_port.port_id],
                                                   host_obj.ingress_port)

    def validate_host_pair_reachability(self, src_h_id, dst_h_id):

        src_host_obj = self.network_graph.get_node_object(src_h_id)
        dst_host_obj = self.network_graph.get_node_object(dst_h_id)

        print "Paths from:", src_h_id, "to:", dst_h_id

        if dst_host_obj.ingress_port.port_id not in src_host_obj.egress_port.admitted_traffic:
            print "None found."
            return

        at = src_host_obj.egress_port.admitted_traffic[dst_host_obj.ingress_port.port_id]

        # Baseline
        at.print_port_paths()

        return len(at.match_elements)

    def validate_all_host_pair_reachability(self):

        for src_h_id in self.network_graph.get_experiment_host_ids():
            for dst_h_id in self.network_graph.get_experiment_host_ids():
                self.validate_host_pair_reachability(src_h_id, dst_h_id)


    def validate_all_host_pair_backup(self):

        for src_h_id in self.network_graph.get_experiment_host_ids():
            for dst_h_id in self.network_graph.get_experiment_host_ids():

                if src_h_id == dst_h_id:
                    continue

                baseline_num_elements = self.validate_host_pair_reachability(src_h_id, dst_h_id)

                # Now break the edges in the primary path in this host-pair, one-by-one
                for edge in self.network_graph.graph.edges():

                    if edge[0].startswith("h") or edge[1].startswith("h"):
                        continue

                    print "Failing edge:", edge

                    self.port_graph.remove_node_graph_edge(edge[0], edge[1])
                    edge_removed_num_elements = self.validate_host_pair_reachability(src_h_id, dst_h_id)

                    # Add it back
                    self.port_graph.add_node_graph_edge(edge[0], edge[1])
                    edge_added_back_num_elements = self.validate_host_pair_reachability(src_h_id, dst_h_id)

                    # the number of elements should be same in three scenarios for each edge
                    if not(baseline_num_elements == edge_removed_num_elements == edge_added_back_num_elements):
                        print "Backup doesn't exist for:", src_h_id, "->", dst_h_id, "due to edge:", edge
                        return

def main():

    mm = None
    load_config = False
    save_config = True
#    topo_description = ("linear", 2, 1)
#    topo_description = ("ring", 4, 1)
    topo_description = ("linear", 3, 1)

#    controller = "odl"
    controller = "ryu"

    if not load_config and save_config:
        cm = ControllerMan(1, controller=controller)
        controller_port = cm.get_next()
        mm = MininetMan(controller_port, *topo_description)

    # Get a flow validator instance
    ng = NetworkGraph(mininet_man=mm, controller=controller, save_config=save_config, load_config=load_config)

    if not load_config and save_config:
        if controller == "odl":
            mm.setup_mininet_with_odl(ng)
        elif controller == "ryu":
            mm.setup_mininet_with_ryu_router()

    # Refresh the network_graph
    ng.parse_switches()
    fv = FlowValidator(ng)

    # Three steps to happy living:
    fv.init_port_graph()
    fv.add_hosts()
    fv.initialize_admitted_traffic()

    #fv.validate_all_host_pair_reachability()
    # fv.remove_hosts()

    fv.validate_all_host_pair_backup()

    fv.de_init_port_graph()

if __name__ == "__main__":
    main()
