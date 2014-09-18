__author__ = 'Rakesh Kumar'

import networkx as nx

from model.model import Model


class BackupPaths:
    def __init__(self):
        self.model = Model()
        self.graph = self.model.get_node_graph()
        self.host_ids = self.model.get_host_ids()
        self.switch_ids = self.model.get_switch_ids()

    def check_flow_reachability(self, src, dst, node_path):

        # The task of this loop is to examine whether there is a rule,
        #  in the switches along the path, that would admit the path
        #  and pass it to the next switch
        # Assume that there are no host firewalls filtering anything inbound/outbound
        #  The loop below goes from first switch to the second-last switch

        is_reachable = False

        edge_ports_dict = self.graph[node_path[0]][node_path[1]]['edge_ports_dict']
        arriving_port = edge_ports_dict[node_path[1]]

        for i in range(1, len(node_path) - 2):

            node_flow_table = self.graph.node[node_path[i]]["flow_table"]
            edge_ports_dict = self.graph[node_path[i]][node_path[i + 1]]['edge_ports_dict']
            departure_port = edge_ports_dict[node_path[i]]

            print "Checking from node:", node_path[i], "at port:", departure_port, \
                "to node:", node_path[i + 1], "at port:", arriving_port

            #  Will this switch pass traffic along
            is_reachable = node_flow_table.passes_flow(arriving_port, src, dst, departure_port)


            # If flow fails to pass, just break, otherwise keep going to the next hop
            if not is_reachable:
                break

            # If flow arrived on the next hop, keep track of which port it arrived on
            arriving_port = edge_ports_dict[node_path[i + 1]]

        return is_reachable


    def analyze_all_node_pairs(self):

        print "Hosts in the graph:", self.host_ids
        print "Switches in the graph:", self.switch_ids
        print "Number of nodes add in the graph:", self.graph.number_of_nodes()

        print "Checking for backup paths between all possible host pairs..."
        for src_host_id in self.host_ids:
            for dst_host_id in self.host_ids:

                # Ignore paths with same src/dst
                if src_host_id == dst_host_id:
                    continue

                print "----------------------------------------------------"
                print 'Paths from', src_host_id, 'to', dst_host_id
                total_paths = 0

                asp = nx.all_simple_paths(self.graph, source=src_host_id, target=dst_host_id)
                for p in asp:
                    print "--"
                    print "Topological Path:", p
                    is_reachable_flow = self.check_flow_reachability(src_host_id, dst_host_id, p)
                    print "is_reachable_flow:", is_reachable_flow
                    if is_reachable_flow:
                        total_paths += 1

                print "--"
                print "total_paths:", total_paths


def main():
    bp = BackupPaths()
    bp.analyze_all_node_pairs()


if __name__ == "__main__":
    main()
