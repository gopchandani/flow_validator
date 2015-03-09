__author__ = 'Rakesh Kumar'


from model.model import Model
from model.match import Traffic

class ComputePaths:
    def __init__(self):
        self.model = Model(init_port_graph=True)
        self.port_graph = self.model.port_graph

    def analyze_all_node_pairs(self):

        # Attach a destination port for each host.
        for host_id in self.model.get_host_ids():
            host_obj = self.model.get_node_object(host_id)

            admitted_match = Traffic(init_wildcard=True)
            admitted_match.set_field("ethernet_type", 0x0800)
            dst_mac_int = int(host_obj.mac_addr.replace(":", ""), 16)
            admitted_match.set_field("ethernet_destination", dst_mac_int)

            self.port_graph.add_destination_host_port_traffic(host_obj, admitted_match)

        for host_id in self.model.get_host_ids():
            host_obj = self.model.get_node_object(host_id)

            # Test 1 trying to reach 3 only, so don't propagate admitted_match from openflow:1
            if host_obj.switch_id == "openflow:1":
                continue

            print "Computing admitted_match:", host_id, "connected to switch:", \
                host_obj.switch_id, "at port:", \
                host_obj.switch_port_attached

            self.port_graph.compute_admitted_match(host_obj.switch_egress_port,
                                                   host_obj.port.admitted_match[host_obj.port.port_id],
                                                   host_obj.port,
                                                   host_obj.port)

        # Test connectivity after flows have bled through the port graph
        for src_h_id in self.model.get_host_ids():
            for dst_h_id in self.model.get_host_ids():

                src_port = self.port_graph.get_port(src_h_id)
                dst_port = self.port_graph.get_port(dst_h_id)
                src_host_obj = self.model.get_node_object(src_port.port_id)
                dst_host_obj = self.model.get_node_object(dst_port.port_id)

                # Test 1 trying to reach 3 only
                if src_host_obj.switch_id == "openflow:3":
                    continue

                if src_port != dst_port:
                    am = src_port.admitted_match[dst_port.port_id]
                    am.print_port_paths()

                    #node1 = "openflow:4"
                    #node2 = "openflow:3"

                    node1 = "openflow:1"
                    node2 = "openflow:4"

                    self.model.simulate_edge_removal(node1, node2)
                    self.port_graph.remove_node_graph_edge(node1, node2)

                    am.print_port_paths()

def main():

    bp = ComputePaths()
    bp.analyze_all_node_pairs()

if __name__ == "__main__":
    main()
