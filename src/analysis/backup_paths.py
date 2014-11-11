__author__ = 'Rakesh Kumar'

import networkx as nx
import sys

from model.model import Model
from model.match import Match

class BackupPaths:
    def __init__(self):
        self.model = Model()
        self.graph = self.model.get_node_graph()
        self.host_ids = self.model.get_host_ids()
        self.switch_ids = self.model.get_switch_ids()

    def check_flow_reachability(self, src, dst, node_path, switch_in_port=None):

        # The task of this loop is to examine whether there is a rule,
        #  in the switches along the path, that would admit the path
        #  and pass it to the next switch
        # Assume that there are no host firewalls filtering anything inbound/outbound
        #  The loop below goes from first switch to the second-last switch

        is_reachable = False

        edge_ports_dict = None
        out_port = None
        in_port = None

        # Sanity check -- Check that last node of the node_path is a host, no matter what
        if self.graph.node[node_path[len(node_path) - 1]]["node_type"] != "host":
            raise Exception("The last node in the node_path has to be a host.")

        # Check whether the first node of path is a host or a switch.
        if self.graph.node[node_path[0]]["node_type"] == "host":

            #Traffic arrives from the host to first switch at switch's port


            edge_ports_dict = self.model.get_edge_port_dict(node_path[0], node_path[1])
            in_port = edge_ports_dict[node_path[1]]

            # Traffic leaves from the first switch's post
            edge_ports_dict = self.model.get_edge_port_dict(node_path[1], node_path[2])
            out_port = edge_ports_dict[node_path[1]]

            node_path = node_path[1:]

        elif self.graph.node[node_path[0]]["node_type"] == "switch":
            if not switch_in_port:
                raise Exception("switching_in_port needed.")

            in_port = switch_in_port
            edge_ports_dict = self.model.get_edge_port_dict(node_path[0], node_path[1])
            out_port = edge_ports_dict[node_path[0]]

        # This loop always starts at a switch
        for i in range(len(node_path) - 1):
            switch = self.graph.node[node_path[i]]["sw"]

            flow_match = Match()
            flow_match.in_port = in_port
            flow_match.src_ip_addr = src
            flow_match.dst_ip_addr = dst

            # is_reachable = switch.passes_flow(flow_match, out_port)
            # if not is_reachable:
            #     break

            switch_out_ports = switch.get_out_ports(flow_match)
            if out_port not in switch_out_ports:
                is_reachable = False
                break
            else:
                is_reachable = True

            # Prepare for next switch along the path if there is a next switch along the path
            if self.graph.node[node_path[i+1]]["node_type"] != "host":

                # Traffic arrives from the host to first switch at switch's port
                edge_ports_dict = self.model.get_edge_port_dict(node_path[i], node_path[i+1])
                in_port = edge_ports_dict[node_path[i+1]]

                # Traffic leaves from the first switch's port
                edge_ports_dict = self.model.get_edge_port_dict(node_path[i+1], node_path[i+2])
                out_port = edge_ports_dict[node_path[i+1]]

        return is_reachable

    def check_flow_backups(self, src, dst, node_path):
        has_backup = False

        # Sanity check -- Check that first node of the node_path is a host, no matter what
        if self.graph.node[node_path[0]]["node_type"] != "host":
            raise Exception("The first node in the node_path has to be a host.")

        # Sanity check -- Check that last node of the node_path is a host, no matter what
        if self.graph.node[node_path[len(node_path) - 1]]["node_type"] != "host":
            raise Exception("The last node in the node_path has to be a host.")

        edge_ports_dict = self.model.get_edge_port_dict(node_path[0], node_path[1])

        in_port = edge_ports_dict[node_path[1]]

        #  Go through the path, one edge at a time

        for i in range(1, len(node_path) - 2):

            edge_has_backup = False

            # Keep a copy of this handy
            edge_ports_dict = self.model.get_edge_port_dict(node_path[i], node_path[i+1])

            # Delete the edge
            self.model.remove_edge(node_path[i], edge_ports_dict[node_path[i]],
                                   node_path[i+1], edge_ports_dict[node_path[i+1]])

            # Go through all simple paths that result when the link breaks
            #  If any of them passes the flow, then this edge has a backup

            asp = nx.all_simple_paths(self.graph, source=node_path[i], target=dst)
            for bp in asp:
                print "Topological Backup Path Candidate:", bp
                edge_has_backup = self.check_flow_reachability(src, dst, bp, in_port)

                print "edge_has_backup:", edge_has_backup
                if edge_has_backup:
                    break

            # Add the edge back and the data that goes along with it
            self.model.add_edge(node_path[i], edge_ports_dict[node_path[i]],
                                node_path[i+1], edge_ports_dict[node_path[i+1]])

            in_port = edge_ports_dict[node_path[i+1]]

            has_backup = edge_has_backup

            if not edge_has_backup:
                break

        return has_backup

    def has_primary_and_backup(self, src_host_id, dst_host_id):
        has_primary_and_backup = False

        #  First grab all topological paths between src/dst hosts
        asp = nx.all_simple_paths(self.graph, source=src_host_id, target=dst_host_id)

        for p in asp:
            print "Topological Primary Path Candidate", p

            is_reachable_flow = self.check_flow_reachability(src_host_id, dst_host_id, p)
            print "is_reachable_flow:", is_reachable_flow

            if is_reachable_flow:
                has_primary_and_backup = self.check_flow_backups(src_host_id, dst_host_id, p)

                # Keep going if this one did not have a backup
                if has_primary_and_backup:
                    break

        return has_primary_and_backup

    def analyze_all_node_pairs(self):

        print "Checking for backup paths between all possible host pairs..."
        for src_host_id in self.host_ids:
            for dst_host_id in self.host_ids:

                # Ignore paths with same src/dst
                if src_host_id == dst_host_id:
                    continue

                print "--------------------------------------------------------------------------------------------------------"
                print 'Checking primary and backup paths from', src_host_id, 'to', dst_host_id
                print "--------------------------------------------------------------------------------------------------------"

                primary_and_backup_exists = self.has_primary_and_backup(src_host_id, dst_host_id)

                print "--------------------------------------------------------------------------------------------------------"
                if primary_and_backup_exists:
                    print "Result: Backup exists."
                else:
                    print "Result:Backup does not exist"


def main():
    bp = BackupPaths()
    bp.analyze_all_node_pairs()


if __name__ == "__main__":
    main()
