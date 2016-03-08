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