__author__ = 'Rakesh Kumar'

from collections import defaultdict
from traffic import Traffic
from port_graph_edge import PortGraphEdge
from port_graph import PortGraph

class SwitchPortGraph(PortGraph):

    def __init__(self, network_graph, sw):

        super(SwitchPortGraph, self).__init__(network_graph)

        self.sw = sw

    def init_switch_port_graph(self):

        print "Initializing Port Graph for switch:", self.sw.node_id

        # Add a node per table in the port graph
        for flow_table in self.sw.flow_tables:
            self.add_node(flow_table.port_graph_node)

        # Add two nodes per physical port in port graph one for incoming and outgoing direction
        # Connect incoming direction port to table 0's port
        for port_num in self.sw.ports:

            port = self.sw.ports[port_num]

            self.add_node(port.port_graph_ingress_node)
            self.add_node(port.port_graph_egress_node)

            incoming_port_match = Traffic(init_wildcard=True)
            incoming_port_match.set_field("in_port", int(port_num))

            self.add_edge_switch_port_graph(port.port_graph_ingress_node,
                          self.sw.flow_tables[0].port_graph_node,
                          None,
                          incoming_port_match,
                          None,
                          None)

        # Try passing a wildcard through the flow table
        for flow_table in self.sw.flow_tables:
            flow_table.init_flow_table_port_graph()

        # Initialize all groups' active buckets
        for group_id in self.sw.group_table.groups:
            self.sw.group_table.groups[group_id].set_active_bucket()

    def de_init_switch_port_graph(self):

        # Try passing a wildcard through the flow table
        for flow_table in self.sw.flow_tables:
            flow_table.de_init_flow_table_port_graph()

        # Remove nodes for physical ports
        for port_num in self.sw.ports:

            port = self.sw.ports[port_num]

            ingress_node = self.get_ingress_node(self.sw.node_id, port_num)
            egress_node = self.get_egress_node(self.sw.node_id, port_num)

            self.remove_edge(ingress_node, self.sw.flow_tables[0].port_graph_node)

            self.remove_node(ingress_node)
            self.remove_node(egress_node)

            del ingress_node
            del egress_node

        # Remove table ports
        for flow_table in self.sw.flow_tables:
            self.remove_node(flow_table.port_graph_node)
            flow_table.port = None
            flow_table.port_graph = None

    def add_edge_switch_port_graph(self,
                 node1,
                 node2,
                 edge_action,
                 edge_filter_match,
                 applied_modifications,
                 written_modifications):

        edge = self.get_edge(node1, node2)
        backup_edge_filter_match = Traffic()

        if edge:
            edge.add_edge_data((edge_filter_match,
                                                 edge_action,
                                                 applied_modifications,
                                                 written_modifications, backup_edge_filter_match))
        else:
            edge = PortGraphEdge(node1, node2)
            edge.add_edge_data((edge_filter_match,
                                    edge_action,
                                    applied_modifications,
                                    written_modifications, backup_edge_filter_match))

            self.add_edge(node1, node2, edge)

        return (node1.node_id, node2.node_id, edge_action)

    def compute_switch_transfer_traffic(self):

        print "Computing Transfer Function for switch:", self.sw.node_id

        # Inject wildcard traffic at each ingress port of the switch
        for port_num in self.sw.ports:

            egress_node = self.get_egress_node(self.sw.node_id, port_num)

            transfer_traffic = Traffic(init_wildcard=True)
            tf_changes = []

            self.compute_port_transfer_traffic(egress_node, transfer_traffic, None, egress_node, tf_changes)

    def account_port_transfer_traffic(self, curr, dst_traffic_at_succ, succ, dst):

        # Keep track of what traffic looks like before any changes occur
        traffic_before_changes = self.get_transfer_traffic(curr, dst)

        # Compute what additional traffic is being admitted overall
        additional_traffic = traffic_before_changes.difference(dst_traffic_at_succ)

        # Do the changes...
        try:
            # First accumulate any more traffic that has arrived from this sucessor
            more_from_succ = curr.transfer_traffic[dst][succ].difference(dst_traffic_at_succ)
            if not more_from_succ.is_empty():
                curr.transfer_traffic[dst][succ].union(more_from_succ)

            # Then get rid of traffic that this particular successor does not admit anymore
            less_from_succ = dst_traffic_at_succ.difference(curr.transfer_traffic[dst][succ])
            if not less_from_succ.is_empty():
                curr.transfer_traffic[dst][succ] = less_from_succ.difference(curr.transfer_traffic[dst][succ])
                if curr.transfer_traffic[dst][succ].is_empty():
                    del curr.transfer_traffic[dst][succ]

        # If there is no traffic for this dst-succ combination prior to this propagation,
        # setup a traffic object for successor
        except KeyError:
            if not dst_traffic_at_succ.is_empty():
                curr.transfer_traffic[dst][succ] = Traffic()
                curr.transfer_traffic[dst][succ].union(dst_traffic_at_succ)

        # Then see what the overall traffic looks like after additional/reduced traffic for specific successor
        traffic_after_changes = self.get_transfer_traffic(curr, dst)

        # Compute what reductions (if any) in traffic has occured due to all the changes
        reduced_traffic = traffic_after_changes.difference(traffic_before_changes)

        # If nothing is left behind then clean up the dictionary.
        if traffic_after_changes.is_empty():
            del curr.transfer_traffic[dst]

        traffic_to_propagate = traffic_after_changes

        return additional_traffic, reduced_traffic, traffic_to_propagate

    def compute_port_transfer_traffic(self, curr, dst_traffic_at_succ, succ, dst, tf_changes):

        additional_traffic, reduced_traffic, traffic_to_propagate = \
            self.account_port_transfer_traffic(curr, dst_traffic_at_succ, succ, dst)

        if not additional_traffic.is_empty():

            # If it is an ingress port, it has no predecessors:

            if curr.node_type == "ingress":
                tf_changes.append((curr, dst, "additional"))

            for pred in self.predecessors_iter(curr):
                edge = self.get_edge(pred, curr)
                pred_transfer_traffic = self.compute_edge_transfer_traffic(traffic_to_propagate, edge)

                # Base case: No traffic left to propagate to predecessors
                if not pred_transfer_traffic.is_empty():
                    self.compute_port_transfer_traffic(pred, pred_transfer_traffic, curr, dst, tf_changes)

        if not reduced_traffic.is_empty():

            if curr.node_type == "ingress":
                tf_changes.append((curr, dst, "removal"))

            for pred in self.predecessors_iter(curr):
                edge = self.get_edge(pred, curr)
                pred_transfer_traffic = self.compute_edge_transfer_traffic(traffic_to_propagate, edge)
                self.compute_port_transfer_traffic(pred, pred_transfer_traffic, curr, dst, tf_changes)

    def compute_edge_transfer_traffic(self, traffic_to_propagate, edge):

        pred_transfer_traffic = Traffic()

        for edge_filter_match, edge_action, applied_modifications, written_modifications, backup_edge_filter_match\
                in edge.edge_data_list:

            if edge_action:
                if not edge_action.is_active:
                    continue

            if edge.edge_type == "egress":

                # Case when traffic changes switch boundary
                traffic_to_propagate.set_field("in_port", is_wildcard=True)

                for te in traffic_to_propagate.traffic_elements:
                    te.instruction_type = edge_action.instruction_type

            if applied_modifications:
                ttp = traffic_to_propagate.get_orig_traffic(applied_modifications)
            else:
                ttp = traffic_to_propagate

            if edge.edge_type == "ingress":
                ttp = traffic_to_propagate.get_orig_traffic()
            else:
                # At all the non-ingress edges accumulate written modifications
                # But these are useless if the instruction_type is applied.
                if written_modifications:
                    for te in ttp.traffic_elements:
                        te.written_modifications.update(written_modifications)

            i = edge_filter_match.intersect(ttp)

            if not i.is_empty():
                pred_transfer_traffic.union(i)

        return pred_transfer_traffic

    def update_port_transfer_traffic_failover_edge_action(self, pred, edge_action, edge_filter_match, tf_changes):

        # See what ports are now muted and unmuted
        muted_port_tuples, unmuted_port_tuple = edge_action.perform_edge_failover()

        for muted_port, bucket_rank in muted_port_tuples:

            prop_traffic = Traffic()
            prop_traffic.union(edge_filter_match)

            muted_egress_node = self.get_egress_node(self.sw.node_id, muted_port.port_number)

            # Mute only if pred has some transfer traffic for the muted_port
            if muted_egress_node in pred.transfer_traffic:
                if muted_egress_node in pred.transfer_traffic[muted_egress_node]:
                    prop_traffic = prop_traffic.difference(pred.transfer_traffic[muted_egress_node][muted_egress_node])

                    for te in prop_traffic.traffic_elements:
                        te.vuln_rank = bucket_rank

                    self.compute_port_transfer_traffic(pred, prop_traffic, muted_egress_node, muted_egress_node, tf_changes)

        if unmuted_port_tuple:
            unmuted_port, bucket_rank = unmuted_port_tuple
            unmuted_egress_node = self.get_egress_node(self.sw.node_id, unmuted_port.port_number)

            prop_traffic = Traffic()
            prop_traffic.union(edge_filter_match)
            try:
                if unmuted_egress_node in pred.transfer_traffic:
                    if unmuted_egress_node in pred.transfer_traffic[unmuted_egress_node]:
                        prop_traffic.union(pred.transfer_traffic[unmuted_egress_node][unmuted_egress_node])
            except KeyError:
                pass

            for te in prop_traffic.traffic_elements:
                te.vuln_rank = bucket_rank

            self.compute_port_transfer_traffic(pred, prop_traffic, unmuted_egress_node, unmuted_egress_node, tf_changes)

    def update_port_transfer_traffic(self, port_num, event_type):

        tf_changes = []

        ingress_node = self.get_ingress_node(self.sw.node_id, port_num)
        egress_node = self.get_egress_node(self.sw.node_id, port_num)

        if event_type == "port_down":

            for pred in self.predecessors_iter(egress_node):
                edge = self.get_edge(pred, egress_node)

                # Go through the edge_data_list, and see if there are any failover actions involved.

                prop_traffic = Traffic()
                for edge_filter_match, edge_action, applied_modifications, written_modifications, backup_edge_filter_match \
                        in edge.edge_data_list:

                    if edge_action.is_failover_action():
                        self.update_port_transfer_traffic_failover_edge_action(pred, edge_action, edge_filter_match, tf_changes)
                    else:
                        prop_traffic.union(edge_filter_match)

                # Take the propagating traffic out of traffic that exists at pred for this egress node
                # The remaining traffic is propagated back from pred.

                if egress_node in pred.transfer_traffic:
                    if egress_node in pred.transfer_traffic[egress_node]:
                        prop_traffic = prop_traffic.difference(pred.transfer_traffic[egress_node][egress_node])

                self.compute_port_transfer_traffic(pred, prop_traffic, egress_node, egress_node, tf_changes)

            # Handle the case of cleaning out muted ports ingress node
            for succ in self.successors_iter(ingress_node):
                edge = self.get_edge(ingress_node, succ)

                for edge_data_tuple in edge.edge_data_list:
                    temp = edge_data_tuple[4].traffic_elements
                    edge_data_tuple[4].traffic_elements = edge_data_tuple[0].traffic_elements
                    edge_data_tuple[0].traffic_elements = temp

            dsts = ingress_node.transfer_traffic.keys()
            for dst in dsts:
                for succ in self.successors_iter(ingress_node):
                    self.compute_port_transfer_traffic(ingress_node, Traffic(), succ, dst, tf_changes)

        elif event_type == "port_up":

            for pred in self.predecessors_iter(egress_node):
                edge = self.get_edge(pred, egress_node)
                prop_traffic = Traffic()

                # Go through the edge_data_list, and see if there are any failover actions involved.
                for edge_filter_match, edge_action, applied_modifications, written_modifications, backup_edge_filter_match \
                        in edge.edge_data_list:

                    if edge_action.is_failover_action():
                        self.update_port_transfer_traffic_failover_edge_action(pred, edge_action, edge_filter_match, tf_changes)
                    else:
                        prop_traffic.union(edge_filter_match)

                # Take the propagating traffic and union any traffic at already exists at the predecessor it
                # and propagate that combined union back from pred.

                if egress_node in pred.transfer_traffic:
                    if egress_node in pred.transfer_traffic[egress_node]:
                        prop_traffic.union(pred.transfer_traffic[egress_node][egress_node])

                self.compute_port_transfer_traffic(pred, prop_traffic, egress_node, egress_node, tf_changes)

            for succ in self.successors_iter(ingress_node):
                edge = self.get_edge(ingress_node, succ)
                for edge_data_tuple in edge.edge_data_list:
                    temp = edge_data_tuple[4].traffic_elements
                    edge_data_tuple[4].traffic_elements = edge_data_tuple[0].traffic_elements
                    edge_data_tuple[0].traffic_elements = temp

                for dst in succ.transfer_traffic.keys():
                    traffic_to_propagate = Traffic()
                    for succ_succ in succ.transfer_traffic[dst]:
                        traffic_to_propagate.union(succ.transfer_traffic[dst][succ_succ])

                    edge = self.get_edge(ingress_node, succ)
                    traffic_to_propagate = self.compute_edge_transfer_traffic(traffic_to_propagate, edge)
                    self.compute_port_transfer_traffic(ingress_node, traffic_to_propagate, succ, dst, tf_changes)

        return tf_changes

    def count_paths(self, this_p, dst_p, verbose, path_str="", path_elements=[]):

        path_count = 0
        if dst_p in this_p.transfer_traffic:
            tt = this_p.transfer_traffic[dst_p]
            for succ_p in tt:
                if succ_p:

                    # Try and detect a loop, if a port repeats more than twice, it is a loop
                    indices = [i for i,x in enumerate(path_elements) if x == succ_p.node_id]
                    if len(indices) > 2:
                        if verbose:
                            print "Found a loop, path_str:", path_str
                    else:
                        path_elements.append(succ_p.node_id)
                        path_count += self.count_paths(succ_p, dst_p, verbose, path_str + " -> " + succ_p.node_id, path_elements)

                # A none succcessor means, it originates here.
                else:
                    if verbose:
                        print path_str

                    path_count += 1

        return path_count

    def count_transfer_function_paths(self, verbose=False):
        path_count = 0

        for src_port_number in self.sw.ports:
            src_p = self.get_ingress_node(self.sw.node_id, src_port_number)
            for dst_port_number in self.sw.ports:
                dst_p = self.get_egress_node(self.sw.node_id, dst_port_number)
                if verbose:
                    print "From Port:", src_port_number, "To Port:", dst_port_number
                path_count += self.count_paths(src_p, dst_p, verbose, src_p.node_id, [src_p.node_id])

                if path_count:
                    tt = src_p.transfer_traffic[dst_p]

        return path_count

    def get_path_counts_and_tt(self, verbose):
        path_count = defaultdict(defaultdict)
        tt = defaultdict(defaultdict)

        for src_port_number in self.sw.ports:
            src_p = self.get_ingress_node(self.sw.node_id, src_port_number)

            for dst_port_number in self.sw.ports:
                dst_p = self.get_egress_node(self.sw.node_id, dst_port_number)

                path_count[src_p][dst_p] = self.count_paths(src_p, dst_p, verbose, src_p.node_id, [src_p.node_id])
                tt[src_p][dst_p] = self.get_transfer_traffic(src_p, dst_p)

        return path_count, tt

    def compare_path_counts_and_tt(self, path_count_before, tt_before, path_count_after, tt_after, verbose):

        all_equal = True

        for src_port_number in self.sw.ports:
            src_p = self.get_ingress_node(self.sw.node_id, src_port_number)

            for dst_port_number in self.sw.ports:
                dst_p = self.get_egress_node(self.sw.node_id, dst_port_number)

                if verbose:
                    print "From Port:", src_port_number, "To Port:", dst_port_number

                if path_count_before[src_p][dst_p] != path_count_after[src_p][dst_p]:
                    print "Path Count mismatch - Before:", path_count_before[src_p][dst_p], \
                        "After:", path_count_after[src_p][dst_p]
                    all_equal = False
                else:
                    if verbose:
                        print "Path Count match - Before:", path_count_before[src_p][dst_p], \
                            "After:", path_count_after[src_p][dst_p]

                if tt_before[src_p][dst_p].is_equal_traffic(tt_after[src_p][dst_p]):
                    if verbose:
                        print "Transfer traffic match"
                else:
                    print "Transfer traffic mismatch"
                    all_equal = False

        return all_equal

    def test_one_port_failure_at_a_time(self, verbose=False):

        test_passed = True

        # Loop over ports of the switch and fail and restore them one by one
        for testing_port_number in self.sw.ports:

            testing_port = self.sw.ports[testing_port_number]

            path_count_before, tt_before = self.get_path_counts_and_tt(verbose)

            testing_port.state = "down"
            tf_changes = self.update_port_transfer_traffic(testing_port_number, "port_down")

            path_count_intermediate, tt_intermediate = self.get_path_counts_and_tt(verbose)

            testing_port.state = "up"
            tf_changes = self.update_port_transfer_traffic(testing_port_number, "port_up")

            path_count_after, tt_after = self.get_path_counts_and_tt(verbose)

            all_equal = self.compare_path_counts_and_tt(path_count_before, tt_before, path_count_after, tt_after, verbose)

            if not all_equal:
                test_passed = all_equal
                print "Test Failed."

        return test_passed