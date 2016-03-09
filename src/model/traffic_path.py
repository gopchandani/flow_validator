__author__ = 'Rakesh Kumar'

class TrafficPath(object):

    def __init__(self, nodes=[], path_edges=[]):
        self.path_nodes = nodes
        self.path_edges = path_edges

        self.max_vuln_rank = self.get_max_vuln_rank()

    def get_max_vuln_rank(self):
        max_vuln_rank = -1

        for edge, enabling_edge_data_list in self.path_edges:
            for enabling_edge_data in enabling_edge_data_list:
                if enabling_edge_data.vuln_rank > max_vuln_rank:
                    max_vuln_rank = enabling_edge_data.vuln_rank

        return max_vuln_rank

    def get_path_links(self):
        path_links = []

        if len(self.path_edges) > 1:
            for i in range(0, len(self.path_edges)):
                edge, enabling_edge_data = self.path_edges[i]
                if edge[0].node_type == 'egress' and edge[1].node_type == 'ingress':
                    path_links.append((edge[0].sw.node_id, edge[1].sw.node_id))

        return path_links

    def __eq__(self, other):

        equal_paths = True

        if len(self.path_nodes) == len(other.path_nodes):
            for i in range(len(self.path_nodes)):
                if self.path_nodes[i] != other.path_nodes[i]:
                    equal_paths = False
                    break
        else:
            equal_paths = False

        return equal_paths

    def __str__(self):
        path_str = ''

        for i in range(len(self.path_nodes) - 1):
            path_str += str(self.path_nodes[i]) + ' -> '

        path_str += str(self.path_nodes[len(self.path_nodes) - 1])

        return path_str

    def __iter__(self):
        for node in self.path_nodes:
            yield node

    def get_len(self):
        return len(self.path_nodes)

    # Returns if the given link fails, the path would have an alternative way to get around
    def path_backup_link(self, ld):

        # Translate the link into equivalent port_graph_node pairs

        # Go to the switch and ask if a backup edge exists in the transfer function
        #  for the traffic carried by this path at that link


        # If so, return the ingress node on the next switch, where that edge leads to
        return True

    def backup_link_checks_out(self, backup_link):
        return True

    def link_failure_causes_disconnect(self, ld):

        causes_disconnect = False
        backup_link = self.path_backup_link(ld)

        if backup_link:

            # If the backup link does not check out, then say that link causes a disconnect and break
            backup_link_checks_out = self.backup_link_checks_out(backup_link)
            if not backup_link_checks_out:
                causes_disconnect = True

        # If any of the flow going through this link does not have a backup, then break
        else:
            causes_disconnect = True

        return causes_disconnect