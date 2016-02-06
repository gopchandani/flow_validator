__author__ = 'Rakesh Kumar'

import networkx as nx

from collections import defaultdict
from traffic import Traffic
from port_graph_edge import PortGraphEdge
from port_graph import get_ingress_node_id, get_egress_node_id

class Switch():

    def __init__(self, sw_id, network_graph):

        self.g = nx.DiGraph()
        self.node_id = sw_id
        self.network_graph = network_graph
        self.flow_tables = []
        self.group_table = None
        self.ports = None
        self.host_ports = []

        # Synthesis stuff
        self.intents = defaultdict(dict)
        self.synthesis_tag = int(self.node_id[1:])

        # Analysis stuff
        self.in_port_match = None
        self.accepted_destination_match = {}

    def init_switch_port_graph(self):

        print "Initializing Port Graph for switch:", self.node_id

        # Add a node per table in the port graph
        for flow_table in self.flow_tables:
            self.add_node(flow_table.port_graph_node)

        # Add two nodes per physical port in port graph one for incoming and outgoing direction
        # Connect incoming direction port to table 0's port
        for port_num in self.ports:

            port = self.ports[port_num]

            self.add_node(port.port_graph_ingress_node)
            self.add_node(port.port_graph_egress_node)

            incoming_port_match = Traffic(init_wildcard=True)
            incoming_port_match.set_field("in_port", int(port_num))

            self.add_edge(port.port_graph_ingress_node,
                          self.flow_tables[0].port_graph_node,
                          None,
                          incoming_port_match,
                          None,
                          None)

        # Try passing a wildcard through the flow table
        for flow_table in self.flow_tables:
            flow_table.init_flow_table_port_graph()

        # Initialize all groups' active buckets
        for group_id in self.group_table.groups:
            self.group_table.groups[group_id].set_active_bucket()

    def de_init_switch_port_graph(self):

        # Try passing a wildcard through the flow table
        for flow_table in self.flow_tables:
            flow_table.de_init_flow_table_port_graph()

        # Remove nodes for physical ports
        for port_num in self.ports:

            port = self.ports[port_num]

            in_p = self.get_ingress_node(self.node_id, port_num)
            out_p = self.get_egress_node(self.node_id, port_num)

            self.remove_edge(in_p, self.flow_tables[0].port_graph_node)

            self.remove_node(in_p)
            self.remove_node(out_p)

            del in_p
            del out_p

        # Remove table ports
        for flow_table in self.flow_tables:
            self.remove_node(flow_table.port_graph_node)
            flow_table.port = None
            flow_table.port_graph = None

    def get_ingress_node(self, node_id, port_number):
        return self.get_node(get_ingress_node_id(node_id, port_number))

    def get_egress_node(self, node_id, port_number):
        return self.get_node(get_egress_node_id(node_id, port_number))

    def add_node(self, node):
        self.g.add_node(node.node_id, p=node)

    def remove_node(self, node):
        self.g.remove_node(node.node_id)

    def get_node(self, node_id):
        return self.g.node[node_id]["p"]

    def add_edge(self,
                 node1,
                 node2,
                 edge_action,
                 edge_filter_match,
                 applied_modifications,
                 written_modifications):

        edge_data = self.g.get_edge_data(node1.node_id, node2.node_id)
        backup_edge_filter_match = Traffic()

        if edge_data:
            edge_data["edge_data"].add_edge_data((edge_filter_match,
                                                 edge_action,
                                                 applied_modifications,
                                                 written_modifications, backup_edge_filter_match))
        else:
            edge_data = PortGraphEdge(node1, node2)
            edge_data.add_edge_data((edge_filter_match,
                                    edge_action,
                                    applied_modifications,
                                    written_modifications, backup_edge_filter_match))

            self.g.add_edge(node1.node_id, node2.node_id, edge_data=edge_data)

        # Take care of any changes that need to be made to the predecessors of node1
        # due to addition of this edge
        #self.update_port_transfer_traffic(node1)

        return (node1.node_id, node2.node_id, edge_action)

    def remove_edge(self, node1, node2):

        # Remove the port-graph edges corresponding to ports themselves
        self.g.remove_edge(node1.node_id, node2.node_id)

        #self.update_port_transfer_traffic(node1)

    def compute_switch_transfer_traffic(self):

        print "Computing Transfer Function for switch:", self.node_id

        # Inject wildcard traffic at each ingress port of the switch
        for port_num in self.ports:

            egress_node = self.get_egress_node(self.node_id, port_num)

            transfer_traffic = Traffic(init_wildcard=True)
            tf_changes = []

            self.compute_port_transfer_traffic(egress_node, transfer_traffic, None, egress_node, tf_changes)


    def account_port_transfer_traffic(self, curr, dst_traffic_at_succ, succ, dst):

        # Keep track of what traffic looks like before any changes occur
        traffic_before_changes = curr.get_dst_transfer_traffic(dst)

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
        traffic_after_changes = curr.get_dst_transfer_traffic(dst)

        # Compute what reductions (if any) in traffic has occured due to all the changes
        reduced_traffic = traffic_after_changes.difference(traffic_before_changes)

        # If nothing is left behind then clean up the dictionary.
        if traffic_after_changes.is_empty():
            del curr.transfer_traffic[dst]

        traffic_to_propagate = traffic_after_changes

        return additional_traffic, reduced_traffic, traffic_to_propagate

    def compute_port_transfer_traffic(self, curr, dst_traffic_at_succ, succ, dst, tf_changes):

        #print "curr:", curr.node_id, "dst:", dst.node_id

        # if curr.node_id == 's19:ingress1' and dst.node_id == 's19:egress6':
        #     pass

        additional_traffic, reduced_traffic, traffic_to_propagate = \
            self.account_port_transfer_traffic(curr, dst_traffic_at_succ, succ, dst)

        if not additional_traffic.is_empty():
            
            # If it is an ingress port, it has no predecessors:
            
            if curr.node_type == "ingress":
                tf_changes.append((curr, dst, "additional"))

            for pred_id in self.g.predecessors_iter(curr.node_id):

                pred = self.get_node(pred_id)
                edge_data = self.g.get_edge_data(pred.node_id, curr.node_id)["edge_data"]
                pred_transfer_traffic = self.compute_edge_transfer_traffic(traffic_to_propagate, edge_data)

                # Base case: No traffic left to propagate to predecessors
                if not pred_transfer_traffic.is_empty():
                    self.compute_port_transfer_traffic(pred, pred_transfer_traffic, curr, dst, tf_changes)

        if not reduced_traffic.is_empty():

            if curr.node_type == "ingress":
                tf_changes.append((curr, dst, "removal"))

            for pred_id in self.g.predecessors_iter(curr.node_id):
                pred = self.get_node(pred_id)
                edge_data = self.g.get_edge_data(pred.node_id, curr.node_id)["edge_data"]
                pred_transfer_traffic = self.compute_edge_transfer_traffic(traffic_to_propagate, edge_data)
                self.compute_port_transfer_traffic(pred, pred_transfer_traffic, curr, dst, tf_changes)

    def compute_edge_transfer_traffic(self, traffic_to_propagate, edge_data):

        pred_transfer_traffic = Traffic()

        for edge_filter_match, edge_action, applied_modifications, written_modifications, backup_edge_filter_match\
                in edge_data.edge_data_list:

            if edge_action:
                if not edge_action.is_active:
                    continue

            if edge_data.edge_type == "egress":

                # Case when traffic changes switch boundary
                traffic_to_propagate.set_field("in_port", is_wildcard=True)

                for te in traffic_to_propagate.traffic_elements:
                    te.instruction_type = edge_action.instruction_type

            if applied_modifications:
                ttp = traffic_to_propagate.get_orig_traffic(applied_modifications)
            else:
                ttp = traffic_to_propagate

            if edge_data.edge_type == "ingress":
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

            muted_egress_node = self.get_egress_node(self.node_id, muted_port.port_number)

            # Mute only if pred has some transfer traffic for the muted_port
            if muted_egress_node in pred.transfer_traffic:
                if muted_egress_node in pred.transfer_traffic[muted_egress_node]:
                    prop_traffic = prop_traffic.difference(pred.transfer_traffic[muted_egress_node][muted_egress_node])

                    for te in prop_traffic.traffic_elements:
                        te.vuln_rank = bucket_rank

                    self.compute_port_transfer_traffic(pred, prop_traffic, muted_egress_node, muted_egress_node, tf_changes)

        if unmuted_port_tuple:
            unmuted_port, bucket_rank = unmuted_port_tuple
            unmuted_egress_node = self.get_egress_node(self.node_id, unmuted_port.port_number)

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

        incoming_port = self.get_ingress_node(self.node_id, port_num)
        egress_node = self.get_egress_node(self.node_id, port_num)

        if event_type == "port_down":

            for dst in egress_node.transfer_traffic:

                for pred_id in self.g.predecessors(egress_node.node_id):
                    pred = self.get_node(pred_id)
                    edge_data = self.g.get_edge_data(pred_id, egress_node.node_id)["edge_data"]

                    prop_traffic = Traffic()
                    for edge_filter_match, edge_action, applied_modifications, written_modifications, backup_edge_filter_match \
                            in edge_data.edge_data_list:

                        if edge_action.is_failover_action():
                            self.update_port_transfer_traffic_failover_edge_action(pred, edge_action, edge_filter_match, tf_changes)
                        else:
                            prop_traffic.union(edge_filter_match)

                    # Mute only if pred has some transfer traffic for the muted_port
                    if egress_node in pred.transfer_traffic:
                        if egress_node in pred.transfer_traffic[egress_node]:
                            prop_traffic = prop_traffic.difference(pred.transfer_traffic[egress_node][egress_node])
                            self.compute_port_transfer_traffic(pred, prop_traffic, egress_node, dst, tf_changes)

            for succ_id in self.g.successors(incoming_port.node_id):
                edge_data = self.g.get_edge_data(incoming_port.node_id, succ_id)["edge_data"]
                for edge_data_tuple in edge_data.edge_data_list:
                    temp = edge_data_tuple[4].traffic_elements
                    edge_data_tuple[4].traffic_elements = edge_data_tuple[0].traffic_elements
                    edge_data_tuple[0].traffic_elements = temp

            dsts = incoming_port.transfer_traffic.keys()
            for dst in dsts:
                for succ_id in self.g.successors(incoming_port.node_id):
                    succ = self.get_node(succ_id)
                    self.compute_port_transfer_traffic(incoming_port, Traffic(), succ, dst, tf_changes)

        elif event_type == "port_up":

            for dst in egress_node.transfer_traffic:

                for pred_id in self.g.predecessors(egress_node.node_id):
                    pred = self.get_node(pred_id)
                    edge_data = self.g.get_edge_data(pred_id, egress_node.node_id)["edge_data"]
                    prop_traffic = Traffic()

                    for edge_filter_match, edge_action, applied_modifications, written_modifications, backup_edge_filter_match \
                            in edge_data.edge_data_list:

                        if edge_action.is_failover_action():
                            self.update_port_transfer_traffic_failover_edge_action(pred, edge_action, edge_filter_match, tf_changes)
                        else:
                            prop_traffic.union(edge_filter_match)

                    try:
                        if egress_node in pred.transfer_traffic:
                            if egress_node in pred.transfer_traffic[egress_node]:
                                prop_traffic.union(pred.transfer_traffic[egress_node][egress_node])
                    except KeyError:
                        pass

                    self.compute_port_transfer_traffic(pred, prop_traffic, egress_node, dst, tf_changes)

            for succ_id in self.g.successors(incoming_port.node_id):
                edge_data = self.g.get_edge_data(incoming_port.node_id, succ_id)["edge_data"]
                for edge_data_tuple in edge_data.edge_data_list:
                    temp = edge_data_tuple[4].traffic_elements
                    edge_data_tuple[4].traffic_elements = edge_data_tuple[0].traffic_elements
                    edge_data_tuple[0].traffic_elements = temp

                succ = self.get_node(succ_id)

                for dst in succ.transfer_traffic.keys():
                    traffic_to_propagate = Traffic()
                    for succ_succ in succ.transfer_traffic[dst]:
                        traffic_to_propagate.union(succ.transfer_traffic[dst][succ_succ])

                    edge_data = self.g.get_edge_data(incoming_port.node_id, succ_id)["edge_data"]
                    traffic_to_propagate = self.compute_edge_transfer_traffic(traffic_to_propagate, edge_data)
                    self.compute_port_transfer_traffic(incoming_port, traffic_to_propagate, succ, dst, tf_changes)

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

        for src_port_number in self.ports:
            src_p = self.get_ingress_node(self.node_id, src_port_number)
            for dst_port_number in self.ports:
                dst_p = self.get_egress_node(self.node_id, dst_port_number)
                if verbose:
                    print "From Port:", src_port_number, "To Port:", dst_port_number
                path_count += self.count_paths(src_p, dst_p, verbose, src_p.node_id, [src_p.node_id])

                if path_count:
                    tt = src_p.transfer_traffic[dst_p]

        return path_count

    def get_path_counts_and_tt(self, verbose):
        path_count = defaultdict(defaultdict)
        tt = defaultdict(defaultdict)

        for src_port_number in self.ports:
            src_p = self.get_ingress_node(self.node_id, src_port_number)

            for dst_port_number in self.ports:
                dst_p = self.get_egress_node(self.node_id, dst_port_number)

                path_count[src_p][dst_p] = self.count_paths(src_p, dst_p, verbose, src_p.node_id, [src_p.node_id])
                tt[src_p][dst_p] = src_p.get_dst_transfer_traffic(dst_p)

        return path_count, tt

    def compare_path_counts_and_tt(self, path_count_before, tt_before, path_count_after, tt_after, verbose):

        all_equal = True

        for src_port_number in self.ports:
            src_p = self.get_ingress_node(self.node_id, src_port_number)

            for dst_port_number in self.ports:
                dst_p = self.get_egress_node(self.node_id, dst_port_number)

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
        for testing_port_number in self.ports:

            testing_port = self.ports[testing_port_number]

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