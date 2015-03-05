__author__ = 'Rakesh Kumar'


from model.model import Model
from model.match import Match

class ComputePortPaths:
    def __init__(self):
        self.model = Model(init_port_graph=True)
        self.port_graph = self.model.port_graph

    def analyze_all_node_pairs(self):

        # Attach a destination port for each host.
        for host_id in self.model.get_host_ids():
            host_obj = self.model.get_node_object(host_id)

            print "Setting admitted_match:", host_id, "connected to switch:", \
                host_obj.switch_id, "at port:", \
                host_obj.switch_port_attached

            admitted_match = Match(init_wildcard=True)
            admitted_match.set_field("ethernet_type", 0x0800)
            dst_mac_int = int(host_obj.mac_addr.replace(":", ""), 16)
            admitted_match.set_field("ethernet_destination", dst_mac_int)
            host_port = self.port_graph.add_destination_host_port_traffic(host_obj, admitted_match)

        #
        # node1 = "openflow:4"
        # node2 = "openflow:3"
        # self.model.simulate_edge_removal(node1, node2)
        # self.port_graph.remove_node_graph_edge(node1, node2)

        # Let the port traffic bleed through to all other ports
        for host_port in self.port_graph.added_host_ports:
            host_obj = self.model.get_node_object(host_port.port_id)
            if host_obj.switch_id == "openflow:1":
                continue

            self.port_graph.compute_admitted_match(curr=host_obj.switch_egress_port,
                                                   curr_admitted_match=host_port.admitted_match[host_port.port_id],
                                                   succ=host_port,
                                                   dst_port=host_port)

        # Test connectivity after flows have bled through the port graph
        for src_h_id in self.model.get_host_ids():
            for dst_h_id in self.model.get_host_ids():

                src_port = self.port_graph.get_port(src_h_id)
                dst_port = self.port_graph.get_port(dst_h_id)
                src_host_obj = self.model.get_node_object(src_port.port_id)
                dst_host_obj = self.model.get_node_object(dst_port.port_id)

                # Test 1 trying to reach 3
                if src_host_obj.switch_id == "openflow:3":
                    continue

                if src_port != dst_port:
                    am = src_port.admitted_match[dst_port.port_id]
                    am.print_traffic_paths()

                    am.print_port_paths()


                    node1 = "openflow:4"
                    node2 = "openflow:3"
                    #
                    # node1 = "openflow:1"
                    # node2 = "openflow:4"

                    self.model.simulate_edge_removal(node1, node2)
                    self.port_graph.remove_node_graph_edge(node1, node2)

                    #am.print_traffic_paths()


def main():

    bp = ComputePortPaths()
    bp.analyze_all_node_pairs()

if __name__ == "__main__":
    main()
