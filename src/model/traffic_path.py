__author__ = 'Rakesh Kumar'

from traffic import Traffic


class TrafficPath(object):

    def __init__(self, port_graph, nodes=None, path_edges=None):

        self.port_graph = port_graph

        if nodes:
            self.path_nodes = nodes
        else:
            self.path_nodes = []

        if path_edges:
            self.path_edges = path_edges
        else:
            self.path_edges = []

        if path_edges and not nodes:
            self.populate_nodes_using_edges(self.path_edges)

        if self.path_nodes:
            self.src_node = self.path_nodes[0]
            self.dst_node = self.path_nodes[len(self.path_nodes) - 1]

    def compare_using_nodes_ids(self, other_node_ids):
        equal_paths = True

        for i in range(len(other_node_ids)):
            if other_node_ids[i] != self.path_nodes[i].node_id:
                equal_paths = False
                break

        return equal_paths

    def populate_nodes_using_edges(self, path_edges):

        # Add the first node
        self.path_nodes.append(path_edges[0][0][0])

        if len(path_edges) > 1:
            for i in range(len(path_edges) - 1):
                if path_edges[i][0][1] == path_edges[i+1][0][0]:
                    self.path_nodes.append(path_edges[i][0][1])
                else:
                    print path_edges[i][0][1]
                    print path_edges[i+1][0][0]
                    raise Exception("Found unexpected sequence of edge nodes that does not chain together")

        # Add the last node in the path
        self.path_nodes.append(path_edges[len(path_edges) - 1][0][1])

    def get_max_active_rank(self):
        max_active_rank = -1

        for edge, enabling_edge_data_list, traffic_at_pred in self.path_edges:
            for enabling_edge_data in enabling_edge_data_list:
                current_edge_data_active_rank = enabling_edge_data.get_active_rank()
                if current_edge_data_active_rank > max_active_rank:
                    max_active_rank = current_edge_data_active_rank

        return max_active_rank

    def get_min_active_rank(self):
        min_active_rank = 99999

        for edge, enabling_edge_data_list, traffic_at_pred in self.path_edges:
            for enabling_edge_data in enabling_edge_data_list:
                current_edge_data_active_rank = enabling_edge_data.get_active_rank()
                if current_edge_data_active_rank < min_active_rank:
                    min_active_rank = current_edge_data_active_rank

        return min_active_rank

    def get_max_min_active_rank(self):
        max_min_active_rank = -1

        for edge, enabling_edge_data_list, traffic_at_pred in self.path_edges:

            min_active_rank = 10000

            for enabling_edge_data in enabling_edge_data_list:
                current_edge_data_active_rank = enabling_edge_data.get_min_active_rank()
                if current_edge_data_active_rank < min_active_rank:
                    min_active_rank = current_edge_data_active_rank

            if min_active_rank > max_min_active_rank:
                max_min_active_rank = min_active_rank

        return max_min_active_rank

    def is_active(self):

        is_active = True

        min_active_rank = self.get_min_active_rank()
        max_active_rank = self.get_max_active_rank()

        if min_active_rank == 0 and max_active_rank == 0:
            is_active = True

        return is_active

    def get_path_links(self):
        path_links = []

        if len(self.path_edges) > 1:
            for i in range(0, len(self.path_edges)):
                edge, enabling_edge_data, traffic_at_pred = self.path_edges[i]
                if edge[0].node_type == 'egress' and edge[1].node_type == 'ingress':
                    path_ld = self.port_graph.network_graph.get_link_data(edge[0].sw.node_id, edge[1].sw.node_id)
                    path_links.append(path_ld)

        return path_links

    def is_path_affected(self, failed_link):
        prior_edges = []
        affected_edge = None

        # Assumes that there is going to be at least one prior edge here.
        for i in range(0, len(self.path_edges)):

            f_edge_tuple, f_enabling_edge_data, f_traffic_at_pred = self.path_edges[i]

            failed_edge_tuple = (f_edge_tuple[0].node_id, f_edge_tuple[1].node_id)

            # If this path actually gets affected by this link's failure...
            if ((failed_edge_tuple == failed_link.forward_port_graph_edge) or
                    (failed_edge_tuple == failed_link.reverse_port_graph_edge)):
                affected_edge = self.path_edges[i - 1]
                prior_edges.pop()
                break
            else:
                prior_edges.append(self.path_edges[i])

        return prior_edges, affected_edge

    def passes_link(self, ld_to_check):
        passes = False
        path_links = self.get_path_links()

        for ld in path_links:
            if ld == ld_to_check:
                passes = True
                break

        return passes

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

    def __len__(self):
        return len(self.path_nodes)
