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
            self.model.simulate_remove_edge(host_id, host_obj.switch_id)
            self.port_graph.remove_node_graph_edge(host_id, host_obj.switch_id)

    def initialize_admitted_traffic(self):

        for host_id in self.model.get_host_ids():
            host_obj = self.model.get_node_object(host_id)

            #print "Computing admitted_traffic:", host_id, "connected to switch:", \
            #    host_obj.switch_id, "at port:", \
            #    host_obj.switch_port_attached

            switch_egress_port = self.port_graph.get_port(self.port_graph.g.predecessors(host_obj.ingress_port.port_id)[0])


            self.port_graph.compute_admitted_traffic(switch_egress_port,
                                                   host_obj.ingress_port.admitted_traffic[host_obj.ingress_port.port_id],
                                                   host_obj.ingress_port)

    # returns list of length of admitted matches
    def admitted_traffic_lengths(self):

        admitted_lengths = []

        for src_h_id in self.model.get_host_ids():
            for dst_h_id in self.model.get_host_ids():

                src_host_obj = self.model.get_node_object(src_h_id)
                dst_host_obj = self.model.get_node_object(dst_h_id)

                if src_h_id != dst_h_id:
                    if dst_host_obj.ingress_port.port_id in src_host_obj.egress_port.admitted_traffic:
                        at = src_host_obj.egress_port.admitted_traffic[dst_host_obj.ingress_port.port_id]
                        admitted_lengths.append(len(at.match_elements))
                    else:
                        admitted_lengths.append(0)

        return admitted_lengths

    def validate_all_host_pair_basic_reachability(self):

        # Test connectivity after flows have bled through the port graph
        for src_h_id in self.model.get_host_ids():
            for dst_h_id in self.model.get_host_ids():

                src_host_obj = self.model.get_node_object(src_h_id)
                dst_host_obj = self.model.get_node_object(dst_h_id)

                if src_h_id != dst_h_id:

                    #print "Port Paths from:", src_h_id, "to:", dst_h_id
                    at = src_host_obj.egress_port.admitted_traffic[dst_host_obj.ingress_port.port_id]

                    # Baseline
                    #at.print_port_paths()

    def validate_all_host_pair_backup_reachability(self, primary_path_edge_dict):

        for host_pair in primary_path_edge_dict:

            src_host_obj = self.model.get_node_object(host_pair[0])
            dst_host_obj = self.model.get_node_object(host_pair[1])

            at = src_host_obj.egress_port.admitted_traffic[dst_host_obj.ingress_port.port_id]

            # Baseline
            baseline_num_elements = len(at.match_elements)

            # Now break the edges in the primary path in this host-pair, one-by-one
            for primary_edge in primary_path_edge_dict[host_pair]:

                self.model.simulate_remove_edge(primary_edge[0], primary_edge[1])
                self.port_graph.remove_node_graph_edge(primary_edge[0], primary_edge[1])
                at = src_host_obj.egress_port.admitted_traffic[dst_host_obj.ingress_port.port_id]
                edge_removed_num_elements = len(at.match_elements)

                # Add it back
                self.model.simulate_add_edge(primary_edge[0], primary_edge[1])
                self.port_graph.add_node_graph_edge(primary_edge[0], primary_edge[1], True)
                at = src_host_obj.egress_port.admitted_traffic[dst_host_obj.ingress_port.port_id]
                edge_added_back_num_elements = len(at.match_elements)

                # the number of elements should be same in three scenarios for each edge
                if not(baseline_num_elements == edge_removed_num_elements == edge_added_back_num_elements):
                    print "Backup doesn't quite exist between pair:", host_pair, "due to edge:", primary_edge
                    return

def main():

    fv = FlowValidator()

    fv.add_hosts()

    fv.initialize_admitted_traffic()

    fv.validate_all_host_pair_basic_reachability()
    #fv.remove_hosts()
    #fv.validate_all_host_pair_basic_reachability()


if __name__ == "__main__":
    main()
