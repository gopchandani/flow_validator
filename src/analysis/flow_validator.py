__author__ = 'Rakesh Kumar'


from model.model import Model
from model.traffic import Traffic

class FlowValidator:

    def __init__(self):
        self.model = Model(init_port_graph=True)
        self.port_graph = self.model.port_graph

    def add_hosts(self):

        # Attach a destination port for each host.
        for host_id in self.model.get_host_ids():

            host_obj = self.model.get_node_object(host_id)

            self.port_graph.add_port(host_obj.ingress_port)
            self.port_graph.add_port(host_obj.egress_port)

            self.port_graph.add_node_graph_edge(host_id, host_obj.switch_id)

            admitted_traffic = Traffic(init_wildcard=True)
            admitted_traffic.set_field("ethernet_type", 0x0800)
            dst_mac_int = int(host_obj.mac_addr.replace(":", ""), 16)
            admitted_traffic.set_field("ethernet_destination", dst_mac_int)

            admitted_traffic.set_port(host_obj.ingress_port)

            host_obj.ingress_port.admitted_traffic[host_obj.ingress_port.port_id] = admitted_traffic



    def remove_hosts(self):

        for host_id in self.model.get_host_ids():

            host_obj = self.model.get_node_object(host_id)
            if host_obj.switch_id == "openflow:1":
                continue

            self.port_graph.remove_host_port_edges(host_obj)

    def initialize_admitted_match(self):

        for host_id in self.model.get_host_ids():
            host_obj = self.model.get_node_object(host_id)

            print "Computing admitted_traffic:", host_id, "connected to switch:", \
                host_obj.switch_id, "at port:", \
                host_obj.switch_port_attached

            switch_egress_port = self.port_graph.g.predecessors(host_obj.ingress_port.port_id)[0]


            self.port_graph.compute_admitted_traffic(switch_egress_port,
                                                   host_obj.ingress_port.admitted_traffic[host_obj.ingress_port.port_id],
                                                   host_obj.ingress_port,
                                                   host_obj.ingress_port)

    def validate_all_host_pair_basic_reachability(self):

        # Test connectivity after flows have bled through the port graph
        for src_h_id in self.model.get_host_ids():
            for dst_h_id in self.model.get_host_ids():

                src_port = self.port_graph.get_port(src_h_id)
                dst_port = self.port_graph.get_port(dst_h_id)
                src_host_obj = self.model.get_node_object(src_port.port_id)

                if src_port != dst_port:

                    print "Port Paths from:", src_h_id, "to:", dst_h_id

                    am = src_port.admitted_traffic[dst_port.port_id]
                    am.print_port_paths()


    def validate_all_host_pair_backup_reachability(self):

        # Test connectivity after flows have bled through the port graph
        for src_h_id in self.model.get_host_ids():
            for dst_h_id in self.model.get_host_ids():

                src_host_obj = self.model.get_node_object(src_h_id)

                if src_host_obj.switch_id == "openflow:3":
                    continue

                src_port = self.port_graph.get_port(src_h_id)

                if src_h_id != dst_h_id:

                    print "Port Paths from:", src_h_id, "to:", dst_h_id
                    at = src_port.admitted_traffic[dst_h_id]

                    # Baseline
                    at.print_port_paths()

                    # First remove the edge

                    #node1 = "openflow:4"
                    #node2 = "openflow:3"
                    node1 = "openflow:1"
                    node2 = "openflow:4"

                    self.model.simulate_remove_edge(node1, node2)
                    self.port_graph.remove_node_graph_edge(node1, node2)
                    at.print_port_paths()

                    # Add it back
                    self.model.simulate_add_edge(node1, node2)
                    self.port_graph.add_node_graph_edge(node1, node2, True)
                    at.print_port_paths()


def main():

    bp = FlowValidator()

    bp.add_hosts()
    bp.initialize_admitted_match()

    #bp.validate_all_host_pair_basic_reachability()

    #bp.validate_all_host_pair_backup_reachability()

    bp.remove_hosts()

    bp.validate_all_host_pair_backup_reachability()


if __name__ == "__main__":
    main()
