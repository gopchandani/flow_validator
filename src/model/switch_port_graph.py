__author__ = 'Rakesh Kumar'

from traffic import Traffic
from port_graph_edge import PortGraphEdge, SwitchPortGraphEdgeData
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

            self.add_node(port.switch_port_graph_ingress_node)
            self.add_node(port.switch_port_graph_egress_node)

            self.boundary_ingress_nodes.append(port.switch_port_graph_ingress_node)
            self.boundary_egress_nodes.append(port.switch_port_graph_egress_node)

            edge = PortGraphEdge(port.switch_port_graph_ingress_node, self.sw.flow_tables[0].port_graph_node)
            edge_traffic_filter = Traffic()
            edge_traffic_filter.union(port.ingress_node_traffic)
            edge_data = SwitchPortGraphEdgeData(edge_traffic_filter, None, None, None)
            edge.add_edge_data(edge_data)
            self.add_edge(port.switch_port_graph_ingress_node, self.sw.flow_tables[0].port_graph_node, edge)

        # Try passing a wildcard through the flow table
        for flow_table in self.sw.flow_tables:
            flow_table.compute_flow_table_port_graph_edges()
            self.add_flow_table_edges(flow_table)

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

    def get_edges_from_flow_table_edges(self, flow_table, succ):

        edge = PortGraphEdge(flow_table.port_graph_node, succ)

        if succ not in flow_table.current_port_graph_edges:
            pass
        else:
            for edge_data in flow_table.current_port_graph_edges[succ]:

                edge_data = SwitchPortGraphEdgeData(edge_data[0], edge_data[1], edge_data[2], edge_data[3])
                edge.add_edge_data(edge_data)

        return edge

    def add_flow_table_edges(self, flow_table):

        for succ in flow_table.current_port_graph_edges:
            edge = self.get_edges_from_flow_table_edges(flow_table, succ)
            self.add_edge(flow_table.port_graph_node, succ, edge)


    def modify_flow_table_edges(self, flow_table, modified_flow_table_edges):

        for modified_edge in modified_flow_table_edges:
            pred = self.get_node(modified_edge[0])
            succ = self.get_node(modified_edge[1])

            # First remove the edge
            edge = self.get_edge(pred, succ)
            if edge:
                self.remove_edge(pred, succ)

            edge = self.get_edges_from_flow_table_edges(flow_table, succ)
            self.add_edge(flow_table.port_graph_node, succ, edge)

    def compute_switch_admitted_traffic(self):

        print "Computing Transfer Function for switch:", self.sw.node_id

        # Inject wildcard traffic at each ingress port of the switch
        for port_num in self.sw.ports:

            egress_node = self.get_egress_node(self.sw.node_id, port_num)

            dst_traffic_at_succ = Traffic(init_wildcard=True)
            end_to_end_modified_edges = []
            self.compute_admitted_traffic(egress_node, dst_traffic_at_succ, None, egress_node, end_to_end_modified_edges)

    def compute_edge_admitted_traffic(self, traffic_to_propagate, edge):

        pred_admitted_traffic = Traffic()

        for ed in edge.edge_data_list:

            if edge.edge_type == "egress":

                # Case when traffic changes switch boundary
                traffic_to_propagate.set_field("in_port", is_wildcard=True)

                for te in traffic_to_propagate.traffic_elements:
                    if ed.edge_action:
                        te.instruction_type = ed.edge_action.instruction_type

            if ed.applied_modifications:
                ttp = traffic_to_propagate.get_orig_traffic(ed.applied_modifications)
            else:
                ttp = traffic_to_propagate

            if edge.edge_type == "ingress":
                ttp = traffic_to_propagate.get_orig_traffic()
            else:
                # At all the non-ingress edges accumulate written modifications
                # But these are useless if the instruction_type is applied.
                if ed.written_modifications:
                    for te in ttp.traffic_elements:
                        te.written_modifications.update(ed.written_modifications)

            i = ed.edge_filter_traffic.intersect(ttp)

            if not i.is_empty():
                pred_admitted_traffic.union(i)

        return pred_admitted_traffic

    def update_admitted_traffic_due_to_port_state_change(self, port_num, event_type):

        end_to_end_modified_edges = []

        ingress_node = self.get_ingress_node(self.sw.node_id, port_num)
        egress_node = self.get_egress_node(self.sw.node_id, port_num)

        for pred in self.predecessors_iter(egress_node):

            edge = self.get_edge(pred, egress_node)
            flow_table = pred.parent_obj

            # First get the modified edges in this flow_table (edges added/deleted/modified)
            modified_flow_table_edges = flow_table.update_port_graph_edges()

            self.modify_flow_table_edges(flow_table, modified_flow_table_edges)

            self.update_admitted_traffic(modified_flow_table_edges, end_to_end_modified_edges)

        if event_type == "port_down":

            edge = self.get_edge(ingress_node, self.sw.flow_tables[0].port_graph_node)
            for ed in edge.edge_data_list:
                del ed.edge_filter_traffic.traffic_elements[:]

            modified_flow_table_edges = [(ingress_node.node_id, self.sw.flow_tables[0].port_graph_node.node_id)]
            self.update_admitted_traffic(modified_flow_table_edges, end_to_end_modified_edges)

        elif event_type == "port_up":

            edge = self.get_edge(ingress_node, self.sw.flow_tables[0].port_graph_node)
            for ed in edge.edge_data_list:
                ed.edge_filter_traffic.union(ingress_node.parent_obj.ingress_node_traffic)

            modified_flow_table_edges = [(ingress_node.node_id, self.sw.flow_tables[0].port_graph_node.node_id)]
            self.update_admitted_traffic(modified_flow_table_edges, end_to_end_modified_edges)

        return end_to_end_modified_edges

    def test_one_port_failure_at_a_time(self, verbose=False):

        test_passed = True

        # Loop over ports of the switch and fail and restore them one by one
        for testing_port_number in self.sw.ports:

            if testing_port_number != 3:
                continue

            testing_port = self.sw.ports[testing_port_number]

            graph_paths_before = self.get_graph_paths(verbose)
            graph_ats_before = self.get_graph_ats()

            testing_port.state = "down"
            end_to_end_modified_edges = self.update_admitted_traffic_due_to_port_state_change(testing_port_number,
                                                                                              "port_down")

            graph_paths_intermediate = self.get_graph_paths(verbose)
            graph_ats_intermediate = self.get_graph_ats()

            testing_port.state = "up"
            end_to_end_modified_edges = self.update_admitted_traffic_due_to_port_state_change(testing_port_number,
                                                                                              "port_up")

            graph_paths_after = self.get_graph_paths(verbose)
            graph_ats_after = self.get_graph_ats()

            all_graph_paths_equal = self.compare_graph_paths(graph_paths_before,
                                                             graph_paths_after,
                                                             verbose)

            if not all_graph_paths_equal:
                test_passed = all_graph_paths_equal
                print "Test Failed."

            all_graph_ats_equal = self.compare_graph_ats(graph_ats_before,
                                                         graph_ats_after,
                                                         verbose)
            if not all_graph_ats_equal:
                test_passed = all_graph_ats_equal
                print "Test Failed."

        return test_passed