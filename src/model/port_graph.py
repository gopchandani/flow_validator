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

    def add_switch_transfer_function(self, sw):

        # First grab the port objects from the sw's node graph and add them to port_graph's node graph
        for port in sw.ports:

            self.add_port(sw.get_port(self.get_incoming_port_id(sw.node_id, port)))
            self.add_port(sw.get_port(self.get_outgoing_port_id(sw.node_id, port)))

        # Add edges from all possible source/destination ports
        for src_port_number in sw.ports:

            src_p = self.get_port(self.get_incoming_port_id(sw.node_id, src_port_number))

            for dst_p in src_p.transfer_traffic:

                traffic_filter = src_p.transfer_traffic[dst_p]
                total_traffic = Traffic()
                for succ in traffic_filter:
                    total_traffic.union(traffic_filter[succ])
                self.add_edge(src_p, dst_p, total_traffic)

    def update_admitted_traffic(self, tf_changes):

        # This object holds for each ingress_port/destination combinations
        # that have changed as keys and list of egress ports as values
        change_matrix = defaultdict(defaultdict)

        for change in tf_changes:

            ingress_p = change[0]
            egress_p = change[1]

            # Modify the edge filter
            edge_data = self.modify_edge(ingress_p, egress_p)

            #TODO Limit the destinations (get them passed by tf_changes)
            for dst_p in ingress_p.admitted_traffic:
                if dst_p not in change_matrix[ingress_p]:
                    change_matrix[ingress_p][dst_p] = [egress_p]
                else:
                    change_matrix[ingress_p][dst_p].append(egress_p)

            for dst_p in egress_p.admitted_traffic:
                if dst_p not in change_matrix[ingress_p]:
                    change_matrix[ingress_p][dst_p] = [egress_p]
                else:
                    change_matrix[ingress_p][dst_p].append(egress_p)

        # Do this for each ingress port that has changed
        for ingress_p in change_matrix:

            # For each destination that may have been affected at the ingress port
            for dst_p in change_matrix[ingress_p]:

                prev_ingress_p_traffic = ingress_p.get_dst_admitted_traffic(dst_p)
                now_ingress_p_traffic = Traffic()

                ingress_p_egress_p_traffic_now = {}

                for egress_p in change_matrix[ingress_p][dst_p]:

                    edge_data = self.g.get_edge_data(ingress_p.port_id, egress_p.port_id)["edge_data"]
                    egress_p_traffic = egress_p.get_dst_admitted_traffic(dst_p)
                    ingress_p_traffic = self.compute_edge_admitted_traffic(egress_p_traffic, edge_data)

                    ingress_p_egress_p_traffic_now[egress_p] = ingress_p_traffic

                    now_ingress_p_traffic.union(ingress_p_traffic)

                more_now = prev_ingress_p_traffic.difference(now_ingress_p_traffic)
                less_now = now_ingress_p_traffic.difference(prev_ingress_p_traffic)

                # Decide if to propagate it, if more_now or less_now is not empty...
                if not more_now.is_empty() or not less_now.is_empty():
                    for egress_p in ingress_p_egress_p_traffic_now:
                        self.compute_admitted_traffic(ingress_p,
                                                      ingress_p_egress_p_traffic_now[egress_p],
                                                      egress_p,
                                                      dst_p)
                else:
                    # Update admitted traffic at ingress port to reflect any and all changes
                    for egress_p in ingress_p_egress_p_traffic_now:
                        ingress_p_traffic = ingress_p_egress_p_traffic_now[egress_p]
                        if ingress_p_traffic.is_empty():
                            if dst_p in ingress_p.admitted_traffic:
                                if egress_p in ingress_p.admitted_traffic[dst_p]:
                                    del ingress_p.admitted_traffic[dst_p][egress_p]
                        else:
                            ingress_p.admitted_traffic[dst_p][egress_p] = ingress_p_traffic

    def init_port_graph(self):

        # Iterate through switches and add the ports and relevant abstract analysis
        for sw in self.network_graph.get_switches():

            sw.init_switch_port_graph()
            sw.compute_switch_transfer_traffic()
            # if sw.node_id == 's2':
            #     sw.test_transfer_function(verbose=True)
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

    def modify_edge(self, src_port, dst_port):

        #TODO: right now, just doing it up by ripping up the edge and putting it back

        self.remove_edge(src_port, dst_port)

        traffic_filter = src_port.transfer_traffic[dst_port]
        total_traffic = Traffic()
        for succ in traffic_filter:
            total_traffic.union(traffic_filter[succ])

        edge_data = self.add_edge(src_port, dst_port, total_traffic)
        return  edge_data

    def add_node_graph_edge(self, node1_id, node2_id, updating=False):

        edge_port_dict = self.network_graph.get_edge_port_dict(node1_id, node2_id)

        from_port = self.get_port(self.get_outgoing_port_id(node1_id, edge_port_dict[node1_id]))
        to_port = self.get_port(self.get_incoming_port_id(node2_id, edge_port_dict[node2_id]))
        from_port.state = "up"
        to_port.state = "up"
        self.add_edge(from_port, to_port, Traffic(init_wildcard=True))

        from_port = self.get_port(self.get_outgoing_port_id(node2_id, edge_port_dict[node2_id]))
        to_port = self.get_port(self.get_incoming_port_id(node1_id, edge_port_dict[node1_id]))
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

        from_port = self.get_port(self.get_outgoing_port_id(node1_id, edge_port_dict[node1_id]))
        to_port = self.get_port(self.get_incoming_port_id(node2_id, edge_port_dict[node2_id]))

        from_port.state = "down"
        to_port.state = "down"
        self.remove_edge(from_port, to_port)

        from_port = self.get_port(self.get_outgoing_port_id(node2_id, edge_port_dict[node2_id]))
        to_port = self.get_port(self.get_incoming_port_id(node1_id, edge_port_dict[node1_id]))
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

            # At egress edges, set the in_port of the admitted match for destination to wildcard
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

            i = edge_filter_traffic.intersect(ttp)

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

    def compute_admitted_traffic(self, curr, dst_traffic_at_succ, succ, dst_port, tf_changes=None):

        # if dst_port.port_id == 's5:egress3':
        #     print "Current Port:", curr.port_id, "Preds:", self.g.predecessors(curr.port_id), "dst:", dst_port.port_id

        additional_traffic, reduced_traffic, traffic_to_propagate = \
            self.account_port_admitted_traffic(curr, dst_traffic_at_succ, succ, dst_port)

        if not additional_traffic.is_empty():

            # If it is an ingress port, it has no predecessors:
            if curr.port_type == "ingress":
                if tf_changes != None:
                    tf_changes.append((curr, dst_port, "additional"))

            for pred_id in self.g.predecessors_iter(curr.port_id):

                pred = self.get_port(pred_id)
                edge_data = self.g.get_edge_data(pred.port_id, curr.port_id)["edge_data"]
                pred_transfer_traffic = self.compute_edge_admitted_traffic(traffic_to_propagate, edge_data)

                # Base case: No traffic left to propagate to predecessors
                if not pred_transfer_traffic.is_empty():
                    self.compute_admitted_traffic(pred, pred_transfer_traffic, curr, dst_port, tf_changes)

        if not reduced_traffic.is_empty():

            if curr.port_type == "ingress":
                if tf_changes != None:
                    tf_changes.append((curr, dst_port, "removal"))

            for pred_id in self.g.predecessors_iter(curr.port_id):
                pred = self.get_port(pred_id)
                edge_data = self.g.get_edge_data(pred.port_id, curr.port_id)["edge_data"]
                pred_transfer_traffic = self.compute_edge_admitted_traffic(traffic_to_propagate, edge_data)
                self.compute_admitted_traffic(pred, pred_transfer_traffic, curr, dst_port, tf_changes)

    def count_paths(self, this_p, dst_p, verbose, path_str="", path_elements=[]):

        path_count = 0

        if dst_p in this_p.admitted_traffic:

            tt = this_p.admitted_traffic[dst_p]

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