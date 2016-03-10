__author__ = 'Rakesh Kumar'

class TrafficPath(object):

    def __init__(self, port_graph, nodes=[], path_edges=[]):

        self.port_graph = port_graph
        self.path_nodes = nodes
        self.path_edges = path_edges

        self.src_node = self.path_nodes[0]
        self.dst_node = self.path_nodes[len(self.path_nodes) - 1]

        self.max_vuln_rank = self.get_max_vuln_rank()
        self.max_active_rank = self.get_max_active_rank()


    def get_max_vuln_rank(self):
        max_vuln_rank = -1

        for edge, enabling_edge_data_list, traffic_at_pred in self.path_edges:
            for enabling_edge_data in enabling_edge_data_list:
                if enabling_edge_data.vuln_rank > max_vuln_rank:
                    max_vuln_rank = enabling_edge_data.vuln_rank

        return max_vuln_rank

    def get_max_active_rank(self):
        max_active_rank = -1

        for edge, enabling_edge_data_list, traffic_at_pred in self.path_edges:
            for enabling_edge_data in enabling_edge_data_list:
                if enabling_edge_data.active_rank > max_active_rank:
                    max_active_rank = enabling_edge_data.active_rank

        return max_active_rank


    def get_path_links(self):
        path_links = []

        if len(self.path_edges) > 1:
            for i in range(0, len(self.path_edges)):
                edge, enabling_edge_data, traffic_at_pred = self.path_edges[i]
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
    def get_backup_ingress_nodes_and_traffic(self, ld):

        ingress_nodes_and_traffic = []

        # Find the path_edges that actually get affected by the failure of given link
        for i in range(0, len(self.path_edges)):
            edge, enabling_edge_data, traffic_at_pred = self.path_edges[i]
            edge_tuple = (edge[0].node_id, edge[1].node_id)

            if edge_tuple == ld.forward_port_graph_edge or edge_tuple == ld.reverse_port_graph_edge:

                # Go to the switch and ask if a backup edge exists in the transfer function
                #  for the traffic carried by this path at that link
                p_edge, p_enabling_edge_data, p_traffic_at_pred  = self.path_edges[i - 1]

                backup_succs = self.port_graph.get_succs_with_admitted_traffic_and_vuln_rank(p_edge[0],
                                                                                             p_traffic_at_pred,
                                                                                             1,
                                                                                             self.dst_node)

                # TODO: Compute the ingress node from successor (Assumption, there is always one succ on egress node)
                for succ, traffic in backup_succs:
                    ingress_node = list(self.port_graph.successors_iter(succ))[0]
                    ingress_nodes_and_traffic.append((ingress_node, traffic))

        # If so, return the ingress node on the next switch, where that edge leads to
        return ingress_nodes_and_traffic

    def link_failure_causes_disconnect(self, ld):

        causes_disconnect = False
        backup_ingress_nodes_and_traffic = self.get_backup_ingress_nodes_and_traffic(ld)

        # If there is no backup successors, ld failure causes disconnect
        if not backup_ingress_nodes_and_traffic:
            causes_disconnect = True
        # If there are backup successors, but they are not adequately carrying traffic, ld failure causes disconnect
        else:
            for ingress_node, traffic_to_carry in backup_ingress_nodes_and_traffic:

                # First get what is admitted at this node
                ingress_at = self.port_graph.get_admitted_traffic(ingress_node, self.dst_node)

                # The check if it carries the required traffic
                if not ingress_at.is_subset_traffic(traffic_to_carry):
                    causes_disconnect = True
                    break

        return causes_disconnect