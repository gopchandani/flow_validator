__author__ = 'Rakesh Kumar'

import networkx as nx

from collections import defaultdict
from traffic import Traffic
from port import Port
from edge_data import EdgeData

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

        # Add a node per table in the port graph
        for flow_table in self.flow_tables:

            tp = Port(self,
                      port_type="table",
                      port_id=self.get_table_port_id(self.node_id, flow_table.table_id))

            self.add_port(tp)
            flow_table.port = tp

        # Add two nodes per physical port in port graph one for incoming and outgoing direction
        # Connect incoming direction port to table 0's port
        for port in self.ports:

            in_p = Port(self,
                        port_type="ingress",
                        port_id=self.get_incoming_port_id(self.node_id, port))

            out_p = Port(self,
                         port_type="egress",
                         port_id=self.get_outgoing_port_id(self.node_id, port))

            in_p.state = "up"
            out_p.state = "up"

            in_p.port_number = int(port)
            out_p.port_number = int(port)

            self.add_port(in_p)
            self.add_port(out_p)

            incoming_port_match = Traffic(init_wildcard=True)
            incoming_port_match.set_field("in_port", int(port))

            self.add_edge(in_p,
                          self.flow_tables[0].port,
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
        for port in self.ports:

            in_p = self.get_port(self.get_incoming_port_id(self.node_id, port))
            out_p = self.get_port(self.get_outgoing_port_id(self.node_id, port))

            self.remove_edge(in_p, self.flow_tables[0].port)

            self.remove_port(in_p)
            self.remove_port(out_p)

            del in_p
            del out_p

        # Remove table ports
        # Add a node per table in the port graph
        for flow_table in self.flow_tables:

            tp = self.get_port(self.get_table_port_id(self.node_id, flow_table.table_id))
            self.remove_port(tp)
            flow_table.port = None
            flow_table.port_graph = None
            del tp

    def get_table_port_id(self, switch_id, table_number):
        return switch_id + ":table" + str(table_number)

    def get_incoming_port_id(self, node_id, port_number):
        return node_id + ":ingress" + str(port_number)

    def get_outgoing_port_id(self, node_id, port_number):
        return node_id + ":egress" + str(port_number)

    def add_port(self, port):
        self.g.add_node(port.port_id, p=port)

    def remove_port(self, port):
        self.g.remove_node(port.port_id)

    def get_port(self, port_id):
        return self.g.node[port_id]["p"]

    def add_edge(self,
                 port1,
                 port2,
                 edge_action,
                 edge_filter_match,
                 applied_modifications,
                 written_modifications):

        edge_data = self.g.get_edge_data(port1.port_id, port2.port_id)
        backup_edge_filter_match = Traffic()

        if edge_data:
            edge_data["edge_data"].add_edge_data((edge_filter_match,
                                                 edge_action,
                                                 applied_modifications,
                                                 written_modifications, backup_edge_filter_match))
        else:
            edge_data = EdgeData(port1, port2)
            edge_data.add_edge_data((edge_filter_match,
                                    edge_action,
                                    applied_modifications,
                                    written_modifications, backup_edge_filter_match))

            self.g.add_edge(port1.port_id, port2.port_id, edge_data=edge_data)

        # Take care of any changes that need to be made to the predecessors of port1
        # due to addition of this edge
        #self.update_port_transfer_traffic(port1)

        return (port1.port_id, port2.port_id, edge_action)

    def remove_edge(self, port1, port2):

        # Remove the port-graph edges corresponding to ports themselves
        self.g.remove_edge(port1.port_id, port2.port_id)

        #self.update_port_transfer_traffic(port1)

    def compute_switch_transfer_traffic(self):

        # Inject wildcard traffic at each ingress port of the switch
        for port in self.ports:

            out_p_id = self.get_outgoing_port_id(self.node_id, port)
            out_p = self.get_port(out_p_id)

            transfer_traffic = Traffic(init_wildcard=True)
            tf_changes = []
            self.compute_port_transfer_traffic(out_p, transfer_traffic, None, out_p, tf_changes)

    def account_port_transfer_traffic(self, port, dst_traffic_at_succ, succ, dst_port):

        # Keep track of what traffic looks like before any changes occur
        traffic_before_changes = Traffic()
        for sp in port.transfer_traffic[dst_port]:
            traffic_before_changes.union(port.transfer_traffic[dst_port][sp])

        # Compute what additional traffic is being admitted overall
        additional_traffic = traffic_before_changes.difference(dst_traffic_at_succ)

        # Do the changes...
        try:
            # First accumulate any more traffic that has arrived from this sucessor
            more_from_succ = port.transfer_traffic[dst_port][succ].difference(dst_traffic_at_succ)
            if not more_from_succ.is_empty():
                port.transfer_traffic[dst_port][succ].union(more_from_succ)

            # Then get rid of traffic that this particular successor does not admit anymore
            less_from_succ = dst_traffic_at_succ.difference(port.transfer_traffic[dst_port][succ])
            if not less_from_succ.is_empty():
                port.transfer_traffic[dst_port][succ] = less_from_succ.difference(port.transfer_traffic[dst_port][succ])
                if port.transfer_traffic[dst_port][succ].is_empty():
                    del port.transfer_traffic[dst_port][succ]

        # If there is no traffic for this dst-succ combination prior to this propagation, 
        # setup a traffic object for successor
        except KeyError:
            if not dst_traffic_at_succ.is_empty():
                port.transfer_traffic[dst_port][succ] = Traffic()
                port.transfer_traffic[dst_port][succ].union(dst_traffic_at_succ)

        # Then see what the overall traffic looks like after additional/reduced traffic for specific successor
        traffic_after_changes = Traffic()
        for sp in port.transfer_traffic[dst_port]:
            traffic_after_changes.union(port.transfer_traffic[dst_port][sp])

        # Compute what reductions (if any) in traffic has occured due to all the changes
        reduced_traffic = traffic_after_changes.difference(traffic_before_changes)

        # If nothing is left behind then clean up the dictionary.
        if traffic_after_changes.is_empty():
            del port.transfer_traffic[dst_port]

        traffic_to_propagate = traffic_after_changes

        return additional_traffic, reduced_traffic, traffic_to_propagate

    def compute_port_transfer_traffic(self, curr, dst_traffic_at_succ, succ, dst_port, tf_changes, vuln_rank=0):

        additional_traffic, reduced_traffic, traffic_to_propagate = \
            self.account_port_transfer_traffic(curr, dst_traffic_at_succ, succ, dst_port)

        if not additional_traffic.is_empty():
            
            # If it is an ingress port, it has no predecessors:
            
            if curr.port_type == "ingress":
                tf_changes.append((curr, dst_port, "additional", vuln_rank))

            for pred_id in self.g.predecessors_iter(curr.port_id):

                pred = self.get_port(pred_id)
                edge_data = self.g.get_edge_data(pred.port_id, curr.port_id)["edge_data"]
                pred_transfer_traffic = self.compute_edge_transfer_traffic(traffic_to_propagate, edge_data)

                # Base case: No traffic left to propagate to predecessors
                if not pred_transfer_traffic.is_empty():
                    self.compute_port_transfer_traffic(pred, pred_transfer_traffic, curr, dst_port, tf_changes,
                                                       vuln_rank)

        if not reduced_traffic.is_empty():

            if curr.port_type == "ingress":
                tf_changes.append((curr, dst_port, "removal"))

            for pred_id in self.g.predecessors_iter(curr.port_id):
                pred = self.get_port(pred_id)
                edge_data = self.g.get_edge_data(pred.port_id, curr.port_id)["edge_data"]
                pred_transfer_traffic = self.compute_edge_transfer_traffic(traffic_to_propagate, edge_data)
                self.compute_port_transfer_traffic(pred, pred_transfer_traffic, curr, dst_port, tf_changes,
                                                   vuln_rank)

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
        muted_ports, unmuted_port = edge_action.perform_edge_failover()

        for muted_port_number, bucket_rank in muted_ports:
            muted_port = self.get_port(self.get_outgoing_port_id(self.node_id, muted_port_number))

            prop_traffic = Traffic()
            prop_traffic.union(edge_filter_match)

            # Mute only if pred has some transfer traffic for the muted_port
            if muted_port in pred.transfer_traffic:
                if muted_port in pred.transfer_traffic[muted_port]:
                    prop_traffic = prop_traffic.difference(pred.transfer_traffic[muted_port][muted_port])
                    self.compute_port_transfer_traffic(pred, prop_traffic, muted_port, muted_port, tf_changes,
                                                       vuln_rank=bucket_rank)

        if unmuted_port:
            unmuted_port_number, bucket_rank = unmuted_port
            unmuted_port = self.get_port(self.get_outgoing_port_id(self.node_id, unmuted_port_number))

            prop_traffic = Traffic()
            prop_traffic.union(edge_filter_match)
            try:
                if unmuted_port in pred.transfer_traffic:
                    if unmuted_port in pred.transfer_traffic[unmuted_port]:
                        prop_traffic.union(pred.transfer_traffic[unmuted_port][unmuted_port])
            except KeyError:
                pass
            self.compute_port_transfer_traffic(pred, prop_traffic, unmuted_port, unmuted_port, tf_changes,
                                               vuln_rank=bucket_rank)

    def update_port_transfer_traffic(self, port_num, event_type):
        
        tf_changes = []

        incoming_port = self.get_port(self.get_incoming_port_id(self.node_id, port_num))
        outgoing_port = self.get_port(self.get_outgoing_port_id(self.node_id, port_num))

        if event_type == "port_down":

            for dst in outgoing_port.transfer_traffic:

                for pred_id in self.g.predecessors(outgoing_port.port_id):
                    pred = self.get_port(pred_id)
                    edge_data = self.g.get_edge_data(pred_id, outgoing_port.port_id)["edge_data"]

                    for edge_filter_match, edge_action, applied_modifications, written_modifications, backup_edge_filter_match \
                            in edge_data.edge_data_list:

                        if edge_action.is_failover_action():
                            self.update_port_transfer_traffic_failover_edge_action(pred, edge_action, edge_filter_match, tf_changes)
                        else:

                            prop_traffic = Traffic()
                            prop_traffic.union(edge_filter_match)

                            # Mute only if pred has some transfer traffic for the muted_port
                            if outgoing_port in pred.transfer_traffic:
                                if outgoing_port in pred.transfer_traffic[outgoing_port]:
                                    prop_traffic = prop_traffic.difference(pred.transfer_traffic[outgoing_port][outgoing_port])
                                    self.compute_port_transfer_traffic(pred, Traffic(), outgoing_port, dst, tf_changes)

            for succ_id in self.g.successors(incoming_port.port_id):
                edge_data = self.g.get_edge_data(incoming_port.port_id, succ_id)["edge_data"]
                for edge_data_tuple in edge_data.edge_data_list:
                    temp = edge_data_tuple[4].traffic_elements
                    edge_data_tuple[4].traffic_elements = edge_data_tuple[0].traffic_elements
                    edge_data_tuple[0].traffic_elements = temp

            dsts = incoming_port.transfer_traffic.keys()
            for dst in dsts:
                for succ_id in self.g.successors(incoming_port.port_id):
                    succ = self.get_port(succ_id)
                    self.compute_port_transfer_traffic(incoming_port, Traffic(), succ, dst, tf_changes)

        elif event_type == "port_up":

            for dst in outgoing_port.transfer_traffic:

                for pred_id in self.g.predecessors(outgoing_port.port_id):
                    pred = self.get_port(pred_id)
                    edge_data = self.g.get_edge_data(pred_id, outgoing_port.port_id)["edge_data"]

                    for edge_filter_match, edge_action, applied_modifications, written_modifications, backup_edge_filter_match \
                            in edge_data.edge_data_list:

                        if edge_action.is_failover_action():
                            self.update_port_transfer_traffic_failover_edge_action(pred, edge_action, edge_filter_match, tf_changes)
                        else:

                            prop_traffic = Traffic()
                            prop_traffic.union(edge_filter_match)
                            try:
                                if outgoing_port in pred.transfer_traffic:
                                    if outgoing_port in pred.transfer_traffic[outgoing_port]:
                                        prop_traffic.union(pred.transfer_traffic[outgoing_port][outgoing_port])
                            except KeyError:
                                pass

                            self.compute_port_transfer_traffic(pred, prop_traffic, outgoing_port, dst, tf_changes)

            for succ_id in self.g.successors(incoming_port.port_id):
                edge_data = self.g.get_edge_data(incoming_port.port_id, succ_id)["edge_data"]
                for edge_data_tuple in edge_data.edge_data_list:
                    temp = edge_data_tuple[4].traffic_elements
                    edge_data_tuple[4].traffic_elements = edge_data_tuple[0].traffic_elements
                    edge_data_tuple[0].traffic_elements = temp

                succ = self.get_port(succ_id)

                for dst in succ.transfer_traffic.keys():
                    traffic_to_propagate = Traffic()
                    for succ_succ in succ.transfer_traffic[dst]:
                        traffic_to_propagate.union(succ.transfer_traffic[dst][succ_succ])

                    edge_data = self.g.get_edge_data(incoming_port.port_id, succ_id)["edge_data"]
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
                    indices = [i for i,x in enumerate(path_elements) if x == succ_p.port_id]
                    if len(indices) > 2:
                        if verbose:
                            print "Found a loop, path_str:", path_str
                    else:
                        path_elements.append(succ_p.port_id)
                        path_count += self.count_paths(succ_p, dst_p, verbose, path_str + " -> " + succ_p.port_id, path_elements)

                # A none succcessor means, it originates here.
                else:
                    if verbose:
                        print path_str

                    path_count += 1

        return path_count

    def count_transfer_function_paths(self, verbose=False):
        path_count = 0

        for src_port_number in self.ports:
            src_p = self.get_port(self.get_incoming_port_id(self.node_id, src_port_number))
            for dst_port_number in self.ports:
                dst_p = self.get_port(self.get_outgoing_port_id(self.node_id, dst_port_number))
                if verbose:
                    print "From Port:", src_port_number, "To Port:", dst_port_number
                path_count += self.count_paths(src_p, dst_p, verbose, src_p.port_id, [src_p.port_id])

                if path_count:
                    tt = src_p.transfer_traffic[dst_p]

        return path_count

    def get_path_counts_and_tt(self, verbose):
        path_count = defaultdict(defaultdict)
        tt = defaultdict(defaultdict)

        for src_port_number in self.ports:
            src_p = self.get_port(self.get_incoming_port_id(self.node_id, src_port_number))

            for dst_port_number in self.ports:
                dst_p = self.get_port(self.get_outgoing_port_id(self.node_id, dst_port_number))

                path_count[src_p][dst_p] = self.count_paths(src_p, dst_p, verbose, src_p.port_id, [src_p.port_id])
                tt[src_p][dst_p] = src_p.get_dst_transfer_traffic(dst_p)

        return path_count, tt

    def compare_path_counts_and_tt(self, path_count_before, tt_before, path_count_after, tt_after, verbose):

        all_equal = True

        for src_port_number in self.ports:
            src_p = self.get_port(self.get_incoming_port_id(self.node_id, src_port_number))

            for dst_port_number in self.ports:
                dst_p = self.get_port(self.get_outgoing_port_id(self.node_id, dst_port_number))

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
            testing_egress_port = self.get_port(self.get_outgoing_port_id(self.node_id, testing_port_number))

            # if testing_port_number != 2:
            #     continue

            path_count_before, tt_before = self.get_path_counts_and_tt(verbose)

            testing_egress_port.state = "down"
            tf_changes = self.update_port_transfer_traffic(testing_port_number, "port_down")

            path_count_intermediate, tt_intermediate = self.get_path_counts_and_tt(verbose)

            testing_egress_port.state = "up"
            tf_changes = self.update_port_transfer_traffic(testing_port_number, "port_up")

            path_count_after, tt_after = self.get_path_counts_and_tt(verbose)

            all_equal = self.compare_path_counts_and_tt(path_count_before, tt_before, path_count_after, tt_after, verbose)

            if not all_equal:
                test_passed = all_equal
                print "Test Failed."

        return test_passed