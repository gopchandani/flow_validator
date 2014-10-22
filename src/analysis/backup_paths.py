__author__ = 'Rakesh Kumar'

import networkx as nx
import sys

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

        #  Grabbing the arriving port at the first switch here
        arriving_port = edge_ports_dict[node_path[1]]

        for i in range(1, len(node_path) - 1):

            node_flow_tables = self.graph.node[node_path[i]]["flow_tables"]

            for node_flow_table in node_flow_tables:

                edge_ports_dict = self.graph[node_path[i]][node_path[i + 1]]['edge_ports_dict']
                departure_port = edge_ports_dict[node_path[i]]

                #  Will this switch pass traffic along
                is_reachable = node_flow_table.passes_flow(arriving_port, src, dst, departure_port)

                # If flow table passes, just break, otherwise keep going to the next table
                if is_reachable:
                    break

            # If none of the flow tables were able to pass, then break

            if not is_reachable:
                break

            # If flow arrived on the next hop, keep track of which port it arrived on
            arriving_port = edge_ports_dict[node_path[i + 1]]

        return is_reachable

    def check_flow_backups(self, src, dst, node_path):
        has_backup = False

        #  Go through the path, one edge at a time

        for i in range(1, len(node_path) - 2):

            edge_has_backup = False

            # Keep a copy of this handy
            edge_ports = self.graph[node_path[i]][node_path[i + 1]]['edge_ports_dict']

            # Delete the edge
            self.graph.remove_edge(node_path[i], node_path[i + 1])

            # Go through all simple paths that result when the link breaks
            #  If any of them passes the flow, then this edge has a backup

            asp = nx.all_simple_paths(self.graph, source=node_path[i], target=dst)
            for p in asp:
                print "Topological Backup Path Candidate:", p
                edge_has_backup = self.check_flow_reachability(src, dst, p)

                print "edge_has_backup:", edge_has_backup
                if edge_has_backup:
                    break


            # Add the edge back and the data that goes along with it
            self.graph.add_edge(node_path[i], node_path[i + 1], edge_ports_dict=edge_ports)

            has_backup = edge_has_backup

            if not edge_has_backup:
                break

        return has_backup


    def analyze_all_node_pairs(self):

        print "Checking for backup paths between all possible host pairs..."
        for src_host_id in self.host_ids:
            for dst_host_id in self.host_ids:

                # Ignore paths with same src/dst
                if src_host_id == dst_host_id:
                    continue

                print "----------------------------------------------------"
                print 'Paths from', src_host_id, 'to', dst_host_id
                total_paths_with_backup = 0

                asp = nx.all_simple_paths(self.graph, source=src_host_id, target=dst_host_id)

                for p in asp:
                    print "--"
                    print "Topological Primary Path Candidate", p
                    is_reachable_flow = self.check_flow_reachability(src_host_id, dst_host_id, p)
                    print "is_reachable_flow:", is_reachable_flow

                    if is_reachable_flow:
                        has_backup_flows = self.check_flow_backups(src_host_id, dst_host_id, p)
                        if has_backup_flows:
                            total_paths_with_backup += 1

                print "--"
                print "total_paths:", total_paths_with_backup


def main():
    bp = BackupPaths()
    bp.analyze_all_node_pairs()


if __name__ == "__main__":
    main()
