__author__ = 'Rakesh Kumar'


from model.model import Model
from model.match import Match

class ComputePortPaths:
    def __init__(self):
        self.model = Model(init_port_graph=True)
        self.port_graph = self.model.port_graph

    def check_port_crossing(self, neighbor_obj, node_obj, destination):

        print "At switch:", node_obj.node_id, "Neighbor Switch:", neighbor_obj.node_id

        edge_port_dict = self.model.get_edge_port_dict(neighbor_obj.node_id, node_obj.node_id)

        #Check to see if the requirped destination match can get from neighbor to node
        out_port_match = neighbor_obj.transfer_function_3(node_obj.accepted_destination_match[destination])

        if edge_port_dict[neighbor_obj.node_id] in out_port_match:

            # compute what traffic will arrive from neighbor
            passing_match = out_port_match[edge_port_dict[neighbor_obj.node_id]]

            # Set the match in the neighbor, indicating what passes
            neighbor_obj.accepted_destination_match[destination] = passing_match

            return True
        else:
            return False

    # def bfs_paths(self, start_port, end_port):
    #
    #     queue = [(end_port, [end_port])]
    #
    #     while queue:
    #         node_obj, path = queue.pop(0)
    #
    #         for neighbor in self.port_graph.g.neighbors(node_obj.node_id):
    #             neighbor_obj = self.model.get_node_object(neighbor)
    #
    #             # Consider only nodes that are not in the path accumulated so far
    #             if neighbor_obj not in path:
    #
    #                 # If arrived at the source already, stop
    #                 if neighbor_obj == start_port:
    #                     yield [neighbor_obj] + path
    #
    #                 # Otherwise, can I come from neighbor to here
    #                 else:
    #                     if self.check_port_crossing(neighbor_obj, node_obj, destination):
    #                         queue.append((neighbor_obj, [neighbor_obj] + path))

    def analyze_all_node_pairs(self):

        # Attach a destination port for each host.
        added_host_ports = []
        for host_id in self.model.get_host_ids():
            print "Setting admitted_match:", host_id
            host_obj = self.model.get_node_object(host_id)

            admitted_match = Match(init_wildcard=True, tag="flow")
            admitted_match.set_field("ethernet_type", 0x0800)
            dst_mac_int = int(host_obj.mac_addr.replace(":", ""), 16)
            admitted_match.set_field("ethernet_destination", dst_mac_int)
            host_port = self.port_graph.add_destination_host_port_traffic(host_obj, admitted_match)
            added_host_ports.append(host_port)

        # Let the port traffic bleed through to all other ports
        for host_port in added_host_ports:
            self.port_graph.bfs_paths_2(host_port)

        #  Test connectivity after flows have bled through the port graph
        for src_h_id in self.model.get_host_ids():
            for dst_h_id in self.model.get_host_ids():

                src_port = self.port_graph.get_port(src_h_id)
                dst_port = self.port_graph.get_port(dst_h_id)

                if src_port == dst_port:
                    continue

                if dst_port.port_id in src_port.admitted_match:
                    print src_port.admitted_match[dst_port.port_id]
                else:
                    print "No admission for dst_host:", dst_h_id, "at src host:", src_h_id


def main():
    bp = ComputePortPaths()
    bp.analyze_all_node_pairs()

if __name__ == "__main__":
    main()
