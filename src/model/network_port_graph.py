__author__ = 'Rakesh Kumar'

from port_graph import PortGraph
from port_graph_edge import PortGraphEdge
from traffic import Traffic
from collections import defaultdict

class NetworkPortGraph(PortGraph):

    def __init__(self, network_graph):

        super(NetworkPortGraph, self).__init__(network_graph)

    def add_switch_transfer_edges(self, sw):

        # First grab the port objects from the sw's node graph and add them to port_graph's node graph
        for port in sw.ports:

            self.add_node(sw.port_graph.get_ingress_node(sw.node_id, port))
            self.add_node(sw.port_graph.get_egress_node(sw.node_id, port))

        # Add edges from all possible source/destination ports
        for src_port_number in sw.ports:

            pred = self.get_ingress_node(sw.node_id, src_port_number)

            for succ in pred.transfer_traffic:
                transfer_traffic = sw.port_graph.get_transfer_traffic(pred, succ)
                edge = self.get_edge_from_transfer_traffic(pred, succ, transfer_traffic)
                self.add_edge(pred, succ, edge)

    def modify_switch_transfer_edges(self, sw, tf_changes):

        for tf_change in tf_changes:
            pred = tf_change[0]
            succ = tf_change[1]

            # First remove the edge
            edge = self.get_edge(pred, succ)
            if edge:
                self.remove_edge(pred, succ)

            # Then, add the edge back by using the new transfer traffic now
            transfer_traffic = sw.port_graph.get_transfer_traffic(pred, succ)
            edge = self.get_edge_from_transfer_traffic(pred, succ, transfer_traffic)
            self.add_edge(pred, succ, edge)


    def update_admitted_traffic(self, tf_changes):

        # This object holds for each pred/dst combinations
        # that have changed as keys and list of succ ports as values
        change_matrix = defaultdict(defaultdict)

        for tf_change in tf_changes:

            pred = tf_change[0]
            succ = tf_change[1]

            #TODO Limit the destinations
            for dst in pred.admitted_traffic:
                if dst not in change_matrix[pred]:
                    change_matrix[pred][dst] = [succ]
                else:
                    change_matrix[pred][dst].append(succ)

            for dst in succ.admitted_traffic:
                if dst not in change_matrix[pred]:
                    change_matrix[pred][dst] = [succ]
                else:
                    change_matrix[pred][dst].append(succ)

        # Do this for each pred port that has changed
        for pred in change_matrix:

            # For each destination that may have been affected at the pred port
            for dst in change_matrix[pred]:

                prev_pred_traffic = self.get_admitted_traffic(pred, dst)
                now_pred_traffic = Traffic()

                pred_succ_traffic_now = {}

                for succ in change_matrix[pred][dst]:

                    edge = self.get_edge(pred, succ)
                    succ_traffic = self.get_admitted_traffic(succ, dst)

                    pred_traffic = self.compute_edge_admitted_traffic(succ_traffic, edge)

                    pred_succ_traffic_now[succ] = pred_traffic

                    now_pred_traffic.union(pred_traffic)

                more_now = prev_pred_traffic.difference(now_pred_traffic)
                less_now = now_pred_traffic.difference(prev_pred_traffic)

                # Decide if to propagate it, if more_now or less_now is not empty...
                if not more_now.is_empty() or not less_now.is_empty():
                    for succ in pred_succ_traffic_now:

                        self.compute_admitted_traffic(pred,
                                                      pred_succ_traffic_now[succ],
                                                      succ,
                                                      dst)
                else:
                    # Update admitted traffic at ingress port to reflect any and all changes
                    for succ in pred_succ_traffic_now:
                        pred_traffic = pred_succ_traffic_now[succ]
                        if pred_traffic.is_empty():
                            if dst in pred.admitted_traffic:
                                if succ in pred.admitted_traffic[dst]:
                                    del pred.admitted_traffic[dst][succ]
                        else:
                            pred.admitted_traffic[dst][succ] = pred_traffic

    def init_network_port_graph(self):

        # Iterate through switches and add the ports and relevant abstract analysis
        for sw in self.network_graph.get_switches():

            sw.port_graph.init_switch_port_graph()
            sw.port_graph.compute_switch_transfer_traffic()
            #test_passed = sw.port_graph.test_one_port_failure_at_a_time(verbose=False)
            self.add_switch_transfer_edges(sw)

        # Add edges between ports on node edges, where nodes are only switches.
        for node_edge in self.network_graph.graph.edges():
            if not node_edge[0].startswith("h") and not node_edge[1].startswith("h"):
                self.add_node_graph_edge(node_edge[0], node_edge[1])

    def de_init_network_port_graph(self):

        # Then get rid of the edges in the port graph
        for node_edge in self.network_graph.graph.edges():
            if not node_edge[0].startswith("h") and not node_edge[1].startswith("h"):
                self.remove_node_graph_edge(node_edge[0], node_edge[1])

        # Then de-initialize switch port graph
        for sw in self.network_graph.get_switches():
            sw.port_graph.de_init_switch_port_graph()

    def get_edge_from_transfer_traffic(self, pred, dst, transfer_traffic):

        edge = PortGraphEdge(pred, dst)

        # If the edge filter became empty, reflect that.
        if transfer_traffic.is_empty():
            t = Traffic()
            edge.add_edge_data((t, {}))
        else:
            # Each traffic element has its own edge_data, because of how it might have
            # traveled through the switch and what modifications it may have accumulated
            for te in transfer_traffic.traffic_elements:
                t = Traffic()
                t.add_traffic_elements([te])
                edge.add_edge_data((t, te.switch_modifications))

        return edge

    def add_node_graph_edge(self, node1_id, node2_id, updating=False):

        # Update the physical port representations in network graph objects
        edge_port_dict = self.network_graph.get_edge_port_dict(node1_id, node2_id)
        sw1 = self.network_graph.get_node_object(node1_id)
        sw2 = self.network_graph.get_node_object(node2_id)
        sw1.ports[edge_port_dict[node1_id]].state = "up"
        sw2.ports[edge_port_dict[node2_id]].state = "up"

        # Update port graph
        from_port = self.get_egress_node(node1_id, edge_port_dict[node1_id])
        to_port = self.get_ingress_node(node2_id, edge_port_dict[node2_id])
        edge = self.get_edge_from_transfer_traffic(from_port, to_port, Traffic(init_wildcard=True))
        self.add_edge(from_port, to_port, edge)

        from_port = self.get_egress_node(node2_id, edge_port_dict[node2_id])
        to_port = self.get_ingress_node(node1_id, edge_port_dict[node1_id])
        edge = self.get_edge_from_transfer_traffic(from_port, to_port, Traffic(init_wildcard=True))
        self.add_edge(from_port, to_port, edge)

        # Update transfer and admitted traffic
        if updating:
            tf_changes = sw1.port_graph.update_port_transfer_traffic(edge_port_dict[node1_id], "port_up")
            self.modify_switch_transfer_edges(sw1, tf_changes)
            self.update_admitted_traffic(tf_changes)

            tf_changes = sw2.port_graph.update_port_transfer_traffic(edge_port_dict[node2_id], "port_up")
            self.modify_switch_transfer_edges(sw2, tf_changes)
            self.update_admitted_traffic(tf_changes)

    def remove_node_graph_edge(self, node1_id, node2_id):

        # Update the physical port representations in network graph objects
        edge_port_dict = self.network_graph.get_edge_port_dict(node1_id, node2_id)
        sw1 = self.network_graph.get_node_object(node1_id)
        sw2 = self.network_graph.get_node_object(node2_id)
        sw1.ports[edge_port_dict[node1_id]].state = "down"
        sw2.ports[edge_port_dict[node2_id]].state = "down"

        # Update port graph
        from_port = self.get_egress_node(node1_id, edge_port_dict[node1_id])
        to_port = self.get_ingress_node(node2_id, edge_port_dict[node2_id])
        self.remove_edge(from_port, to_port)

        from_port = self.get_egress_node(node2_id, edge_port_dict[node2_id])
        to_port = self.get_ingress_node(node1_id, edge_port_dict[node1_id])
        self.remove_edge(from_port, to_port)

        # Update transfer and admitted traffic
        tf_changes = sw1.port_graph.update_port_transfer_traffic(edge_port_dict[node1_id], "port_down")
        self.modify_switch_transfer_edges(sw1, tf_changes)
        self.update_admitted_traffic(tf_changes)

        tf_changes = sw2.port_graph.update_port_transfer_traffic(edge_port_dict[node2_id], "port_down")
        self.modify_switch_transfer_edges(sw2, tf_changes)
        self.update_admitted_traffic(tf_changes)


    def compute_edge_admitted_traffic(self, traffic_to_propagate, edge):

        pred_admitted_traffic = Traffic()

        for edge_filter_traffic, modifications in edge.edge_data_list:

            # At succ edges, set the in_port of the admitted match for destination to wildcard
            if edge.edge_type == "outside":
                traffic_to_propagate.set_field("in_port", is_wildcard=True)

            # If there were modifications along the way...
            if modifications:
                # If the edge ports belong to the same switch, keep the modifications, otherwise get rid of them.
                if edge.port1.sw == edge.port2.sw:
                    ttp = traffic_to_propagate.get_orig_traffic(modifications, store_switch_modifications=True)
                else:
                    ttp = traffic_to_propagate.get_orig_traffic(modifications, store_switch_modifications=False)
            else:
                ttp = traffic_to_propagate

            i = edge_filter_traffic.intersect(ttp, take_self_vuln_rank=True)

            if not i.is_empty():
                pred_admitted_traffic.union(i)

        return pred_admitted_traffic

    def account_port_admitted_traffic(self, curr, dst_traffic_at_succ, succ, dst):

        # Keep track of what traffic looks like before any changes occur
        traffic_before_changes = self.get_admitted_traffic(curr, dst)

        # Compute what additional traffic is being admitted overall
        additional_traffic = traffic_before_changes.difference(dst_traffic_at_succ)

        # Do the changes...
        try:
            # First accumulate any more traffic that has arrived from this sucessor
            more_from_succ = curr.admitted_traffic[dst][succ].difference(dst_traffic_at_succ)
            if not more_from_succ.is_empty():
                curr.admitted_traffic[dst][succ].union(more_from_succ)

            # Then get rid of traffic that this particular successor does not admit anymore
            less_from_succ = dst_traffic_at_succ.difference(curr.admitted_traffic[dst][succ])
            if not less_from_succ.is_empty():
                curr.admitted_traffic[dst][succ] = less_from_succ.difference(curr.admitted_traffic[dst][succ])
                if curr.admitted_traffic[dst][succ].is_empty():
                    del curr.admitted_traffic[dst][succ]

        # If there is no traffic for this dst-succ combination prior to this propagation,
        # setup a traffic object for successor
        except KeyError:
            if not dst_traffic_at_succ.is_empty():
                curr.admitted_traffic[dst][succ] = Traffic()
                curr.admitted_traffic[dst][succ].union(dst_traffic_at_succ)

        # Then see what the overall traffic looks like after additional/reduced traffic for specific successor
        traffic_after_changes = self.get_admitted_traffic(curr, dst)

        # Compute what reductions (if any) in traffic has occured due to all the changes
        reduced_traffic = traffic_after_changes.difference(traffic_before_changes)

        # If nothing is left behind then clean up the dictionary.
        if traffic_after_changes.is_empty():
            del curr.admitted_traffic[dst]

        traffic_to_propagate = traffic_after_changes

        return additional_traffic, reduced_traffic, traffic_to_propagate

    def compute_admitted_traffic(self, curr, dst_traffic_at_succ, succ, dst):

        additional_traffic, reduced_traffic, traffic_to_propagate = \
            self.account_port_admitted_traffic(curr, dst_traffic_at_succ, succ, dst)

        if not additional_traffic.is_empty():

            for pred in self.predecessors_iter(curr):

                edge = self.get_edge(pred, curr)
                pred_transfer_traffic = self.compute_edge_admitted_traffic(traffic_to_propagate, edge)

                # Base case: No traffic left to propagate to predecessors
                if not pred_transfer_traffic.is_empty():
                    self.compute_admitted_traffic(pred, pred_transfer_traffic, curr, dst)

        if not reduced_traffic.is_empty():

            for pred in self.predecessors_iter(curr):
                edge = self.get_edge(pred, curr)
                pred_transfer_traffic = self.compute_edge_admitted_traffic(traffic_to_propagate, edge)
                self.compute_admitted_traffic(pred, pred_transfer_traffic, curr, dst)

    def get_paths(self, this_p, dst, specific_traffic, this_path, all_paths, path_vuln_rank, path_vuln_ranks, verbose):

        if dst in this_p.admitted_traffic:

            at = this_p.admitted_traffic[dst]

            # If destination is one of the successors, stop
            if dst in at:
                this_path.append(dst)
                all_paths.append(this_path)
                path_vuln_ranks.append(path_vuln_rank)

            # Otherwise explore all the successors
            else:

                this_path_continues = False

                for succ in at:
                    # Check for loops, if a node repeats more than twice, it is a loop
                    indices = [i for i,x in enumerate(this_path) if x == succ]
                    if len(indices) > 2:
                        print "Found a loop, this_path:", this_path
                    else:
                        if at[succ].is_subset_traffic(specific_traffic):
                            this_path.append(succ)

                            modified_specific_traffic = specific_traffic.intersect(at[succ])
                            modified_specific_traffic = modified_specific_traffic.get_modified_traffic()

                            max_vuln_rank_modified = modified_specific_traffic.get_max_vuln_rank()

                            self.get_paths(succ,
                                           dst,
                                           modified_specific_traffic,
                                           this_path,
                                           all_paths,
                                           path_vuln_rank + max_vuln_rank_modified,
                                           path_vuln_ranks,
                                           verbose)

                            this_path_continues = True

                if not this_path_continues:
                    pass