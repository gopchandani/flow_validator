__author__ = 'Rakesh Kumar'

import networkx as nx
from port import Port
from edge_data import EdgeData
from traffic import Traffic
from collections import defaultdict

class PortGraph:

    def __init__(self, network_graph):

        self.network_graph = network_graph
        self.g = nx.DiGraph()

    def get_table_port_id(self, switch_id, table_number):
        return switch_id + ":table" + str(table_number)

    def get_incoming_port_id(self, node_id, port_number):
        return node_id + ":ingress" + str(port_number)

    def get_incoming_port(self, node_id, port_number):
        return self.get_port(node_id + ":ingress" + str(port_number))

    def get_outgoing_port_id(self, node_id, port_number):
        return node_id + ":egress" + str(port_number)

    def get_outgoing_port(self, node_id, port_number):
        return self.get_port(node_id + ":egress" + str(port_number))

    def add_port(self, port):
        self.g.add_node(port.port_id, p=port)

    def remove_port(self, port):
        self.g.remove_node(port.port_id)

    def get_port(self, port_id):
        return self.g.node[port_id]["p"]

    def add_switch_transfer_function(self, sw):

        # First grab the port objects from the sw's node graph and add them to port_graph's node graph
        for port in sw.ports:

            self.add_port(sw.get_incoming_port(sw.node_id, port))
            self.add_port(sw.get_outgoing_port(sw.node_id, port))

        # Add edges from all possible source/destination ports
        for src_port_number in sw.ports:

            src_p = self.get_incoming_port(sw.node_id, src_port_number)

            for dst_p in src_p.transfer_traffic:

                traffic_filter = src_p.transfer_traffic[dst_p]
                total_traffic = Traffic()
                for succ in traffic_filter:
                    total_traffic.union(traffic_filter[succ])
                self.add_edge(src_p, dst_p, total_traffic)

    def update_admitted_traffic(self, tf_changes):

        # This object holds for each pred_port/destination combinations
        # that have changed as keys and list of succ ports as values
        change_matrix = defaultdict(defaultdict)

        for tf_change in tf_changes:

            pred_p = tf_change[0]
            succ_p = tf_change[1]

            # Modify the edge filter
            edge_data = self.modify_edge(tf_change)

            #TODO Limit the destinations
            for dst_p in pred_p.admitted_traffic:
                if dst_p not in change_matrix[pred_p]:
                    change_matrix[pred_p][dst_p] = [succ_p]
                else:
                    change_matrix[pred_p][dst_p].append(succ_p)

            for dst_p in succ_p.admitted_traffic:
                if dst_p not in change_matrix[pred_p]:
                    change_matrix[pred_p][dst_p] = [succ_p]
                else:
                    change_matrix[pred_p][dst_p].append(succ_p)

        # Do this for each pred port that has changed
        for pred_p in change_matrix:

            # For each destination that may have been affected at the pred port
            for dst_p in change_matrix[pred_p]:

                prev_pred_p_traffic = pred_p.get_dst_admitted_traffic(dst_p)
                now_pred_p_traffic = Traffic()

                pred_p_succ_p_traffic_now = {}

                for succ_p in change_matrix[pred_p][dst_p]:

                    edge_data = self.g.get_edge_data(pred_p.port_id, succ_p.port_id)["edge_data"]
                    succ_p_traffic = succ_p.get_dst_admitted_traffic(dst_p)

                    pred_p_traffic = self.compute_edge_admitted_traffic(succ_p_traffic, edge_data)

                    pred_p_succ_p_traffic_now[succ_p] = pred_p_traffic

                    now_pred_p_traffic.union(pred_p_traffic)

                more_now = prev_pred_p_traffic.difference(now_pred_p_traffic)
                less_now = now_pred_p_traffic.difference(prev_pred_p_traffic)

                # Decide if to propagate it, if more_now or less_now is not empty...
                if not more_now.is_empty() or not less_now.is_empty():
                    for succ_p in pred_p_succ_p_traffic_now:

                        self.compute_admitted_traffic(pred_p,
                                                      pred_p_succ_p_traffic_now[succ_p],
                                                      succ_p,
                                                      dst_p)
                else:
                    # Update admitted traffic at ingress port to reflect any and all changes
                    for succ_p in pred_p_succ_p_traffic_now:
                        pred_p_traffic = pred_p_succ_p_traffic_now[succ_p]
                        if pred_p_traffic.is_empty():
                            if dst_p in pred_p.admitted_traffic:
                                if succ_p in pred_p.admitted_traffic[dst_p]:
                                    del pred_p.admitted_traffic[dst_p][succ_p]
                        else:
                            pred_p.admitted_traffic[dst_p][succ_p] = pred_p_traffic

    def init_port_graph(self):

        # Iterate through switches and add the ports and relevant abstract analysis
        for sw in self.network_graph.get_switches():

            sw.init_switch_port_graph()
            sw.compute_switch_transfer_traffic()

            #if sw.node_id == 's3':
                #test_passed = sw.test_one_port_failure_at_a_time(verbose=False)

            self.add_switch_transfer_function(sw)

        # Add edges between ports on node edges, where nodes are only switches.
        for node_edge in self.network_graph.graph.edges():
            if not node_edge[0].startswith("h") and not node_edge[1].startswith("h"):
                self.add_node_graph_edge(node_edge[0], node_edge[1])

    def de_init_port_graph(self):

        # Then get rid of the edges in the port graph
        for node_edge in self.network_graph.graph.edges():
            if not node_edge[0].startswith("h") and not node_edge[1].startswith("h"):
                self.remove_node_graph_edge(node_edge[0], node_edge[1])

        # Then de-initialize switch port graph
        for sw in self.network_graph.get_switches():
            sw.de_init_switch_port_graph()

    def add_edge(self, src_port, dst_port, edge_filter_traffic):

        edge_data = EdgeData(src_port, dst_port)

        # If the edge filter became empty, reflect that.
        if edge_filter_traffic.is_empty():
            t = Traffic()
            edge_data.add_edge_data((t, {}))
        else:
            # Each traffic element has its own edge_data, because of how it might have
            # traveled through the switch and what modifications it may have accumulated
            for te in edge_filter_traffic.traffic_elements:
                t = Traffic()
                t.add_traffic_elements([te])
                edge_data.add_edge_data((t, te.switch_modifications))

        self.g.add_edge(src_port.port_id, dst_port.port_id, edge_data=edge_data)

        return edge_data

        #self.update_switch_transfer_function(src_port.sw, src_port)

    def remove_edge(self, src_port, dst_port):

        if not self.g.has_edge(src_port.port_id, dst_port.port_id):
            return

        # Remove the port-graph edges corresponding to ports themselves
        self.g.remove_edge(src_port.port_id, dst_port.port_id)

    def modify_edge(self, tf_change):

        src_port = tf_change[0]
        dst_port = tf_change[1]

        self.remove_edge(src_port, dst_port)

        traffic_filter = src_port.transfer_traffic[dst_port]
        total_traffic = Traffic()
        for succ in traffic_filter:
            total_traffic.union(traffic_filter[succ])

        if tf_change[2] == "additional":
            edge_data = self.add_edge(src_port, dst_port, total_traffic)
        else:
            edge_data = self.add_edge(src_port, dst_port, total_traffic)

        return  edge_data

    def add_node_graph_edge(self, node1_id, node2_id, updating=False):

        edge_port_dict = self.network_graph.get_edge_port_dict(node1_id, node2_id)

        from_port = self.get_outgoing_port(node1_id, edge_port_dict[node1_id])
        to_port = self.get_incoming_port(node2_id, edge_port_dict[node2_id])
        from_port.state = "up"
        to_port.state = "up"
        self.add_edge(from_port, to_port, Traffic(init_wildcard=True))

        from_port = self.get_outgoing_port(node2_id, edge_port_dict[node2_id])
        to_port = self.get_incoming_port(node1_id, edge_port_dict[node1_id])
        from_port.state = "up"
        to_port.state = "up"
        self.add_edge(from_port, to_port, Traffic(init_wildcard=True))

        if updating:
            sw1 = self.network_graph.get_node_object(node1_id)
            sw2 = self.network_graph.get_node_object(node2_id)

            tf_changes = sw1.update_port_transfer_traffic(edge_port_dict[node1_id], "port_up")
            self.update_admitted_traffic(tf_changes)

            tf_changes = sw2.update_port_transfer_traffic(edge_port_dict[node2_id], "port_up")
            self.update_admitted_traffic(tf_changes)

    def remove_node_graph_edge(self, node1_id, node2_id):

        edge_port_dict = self.network_graph.get_edge_port_dict(node1_id, node2_id)

        from_port = self.get_outgoing_port(node1_id, edge_port_dict[node1_id])
        to_port = self.get_incoming_port(node2_id, edge_port_dict[node2_id])

        from_port.state = "down"
        to_port.state = "down"
        self.remove_edge(from_port, to_port)

        from_port = self.get_outgoing_port(node2_id, edge_port_dict[node2_id])
        to_port = self.get_incoming_port(node1_id, edge_port_dict[node1_id])
        from_port.state = "down"
        to_port.state = "down"
        self.remove_edge(from_port, to_port)

        sw1 = self.network_graph.get_node_object(node1_id)
        sw2 = self.network_graph.get_node_object(node2_id)

        tf_changes = sw1.update_port_transfer_traffic(edge_port_dict[node1_id], "port_down")
        self.update_admitted_traffic(tf_changes)

        tf_changes = sw2.update_port_transfer_traffic(edge_port_dict[node2_id], "port_down")
        self.update_admitted_traffic(tf_changes)

    def compute_edge_admitted_traffic(self, traffic_to_propagate, edge_data):

        pred_admitted_traffic = Traffic()

        for edge_filter_traffic, modifications in edge_data.edge_data_list:

            # At succ edges, set the in_port of the admitted match for destination to wildcard
            if edge_data.edge_type == "outside":
                traffic_to_propagate.set_field("in_port", is_wildcard=True)

            # If there were modifications along the way...
            if modifications:
                # If the edge ports belong to the same switch, keep the modifications, otherwise get rid of them.
                if edge_data.port1.sw == edge_data.port2.sw:
                    ttp = traffic_to_propagate.get_orig_traffic(modifications, store_switch_modifications=True)
                else:
                    ttp = traffic_to_propagate.get_orig_traffic(modifications, store_switch_modifications=False)
            else:
                ttp = traffic_to_propagate

            i = edge_filter_traffic.intersect(ttp, take_self_vuln_rank=True)

            if not i.is_empty():
                pred_admitted_traffic.union(i)

        return pred_admitted_traffic

    def account_port_admitted_traffic(self, port, dst_traffic_at_succ, succ, dst_port):

        # Keep track of what traffic looks like before any changes occur
        traffic_before_changes = Traffic()
        for sp in port.admitted_traffic[dst_port]:
            traffic_before_changes.union(port.admitted_traffic[dst_port][sp])

        # Compute what additional traffic is being admitted overall
        additional_traffic = traffic_before_changes.difference(dst_traffic_at_succ)

        # Do the changes...
        try:
            # First accumulate any more traffic that has arrived from this sucessor
            more_from_succ = port.admitted_traffic[dst_port][succ].difference(dst_traffic_at_succ)
            if not more_from_succ.is_empty():
                port.admitted_traffic[dst_port][succ].union(more_from_succ)

            # Then get rid of traffic that this particular successor does not admit anymore
            less_from_succ = dst_traffic_at_succ.difference(port.admitted_traffic[dst_port][succ])
            if not less_from_succ.is_empty():
                port.admitted_traffic[dst_port][succ] = less_from_succ.difference(port.admitted_traffic[dst_port][succ])
                if port.admitted_traffic[dst_port][succ].is_empty():
                    del port.admitted_traffic[dst_port][succ]

        # If there is no traffic for this dst-succ combination prior to this propagation,
        # setup a traffic object for successor
        except KeyError:
            if not dst_traffic_at_succ.is_empty():
                port.admitted_traffic[dst_port][succ] = Traffic()
                port.admitted_traffic[dst_port][succ].union(dst_traffic_at_succ)

        # Then see what the overall traffic looks like after additional/reduced traffic for specific successor
        traffic_after_changes = Traffic()
        for sp in port.admitted_traffic[dst_port]:
            traffic_after_changes.union(port.admitted_traffic[dst_port][sp])

        # Compute what reductions (if any) in traffic has occured due to all the changes
        reduced_traffic = traffic_after_changes.difference(traffic_before_changes)

        # If nothing is left behind then clean up the dictionary.
        if traffic_after_changes.is_empty():
            del port.admitted_traffic[dst_port]

        traffic_to_propagate = traffic_after_changes

        return additional_traffic, reduced_traffic, traffic_to_propagate

    def compute_admitted_traffic(self, curr, dst_traffic_at_succ, succ, dst_port):

        additional_traffic, reduced_traffic, traffic_to_propagate = \
            self.account_port_admitted_traffic(curr, dst_traffic_at_succ, succ, dst_port)

        if not additional_traffic.is_empty():

            for pred_id in self.g.predecessors_iter(curr.port_id):

                pred = self.get_port(pred_id)
                edge_data = self.g.get_edge_data(pred.port_id, curr.port_id)["edge_data"]
                pred_transfer_traffic = self.compute_edge_admitted_traffic(traffic_to_propagate, edge_data)

                # Base case: No traffic left to propagate to predecessors
                if not pred_transfer_traffic.is_empty():
                    self.compute_admitted_traffic(pred, pred_transfer_traffic, curr, dst_port)

        if not reduced_traffic.is_empty():

            for pred_id in self.g.predecessors_iter(curr.port_id):
                pred = self.get_port(pred_id)
                edge_data = self.g.get_edge_data(pred.port_id, curr.port_id)["edge_data"]
                pred_transfer_traffic = self.compute_edge_admitted_traffic(traffic_to_propagate, edge_data)
                self.compute_admitted_traffic(pred, pred_transfer_traffic, curr, dst_port)

    def get_paths(self, this_p, dst_p, specific_traffic, this_path, all_paths, path_vuln_rank, path_vuln_ranks, verbose):

        if dst_p in this_p.admitted_traffic:

            at = this_p.admitted_traffic[dst_p]

            # If destination is one of the successors, stop
            if dst_p in at:
                this_path.append(dst_p)
                all_paths.append(this_path)
                path_vuln_ranks.append(path_vuln_rank)

            # Otherwise explore all the successors
            else:

                this_path_continues = False

                for succ_p in at:
                    # Check for loops, if a port repeats more than twice, it is a loop
                    indices = [i for i,x in enumerate(this_path) if x == succ_p]
                    if len(indices) > 2:
                        print "Found a loop, this_path:", this_path
                    else:
                        if at[succ_p].is_subset_traffic(specific_traffic):
                            this_path.append(succ_p)

                            modified_specific_traffic = specific_traffic.intersect(at[succ_p])
                            modified_specific_traffic = modified_specific_traffic.get_modified_traffic()

                            max_vuln_rank_modified = modified_specific_traffic.get_max_vuln_rank()

                            self.get_paths(succ_p,
                                           dst_p,
                                           modified_specific_traffic,
                                           this_path,
                                           all_paths,
                                           path_vuln_rank + max_vuln_rank_modified,
                                           path_vuln_ranks,
                                           verbose)

                            this_path_continues = True

                if not this_path_continues:
                    pass