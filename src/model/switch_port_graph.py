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

        # Initialize switch ports' port graph state
        for port_num in self.sw.ports:

            if port_num == 1 and self.sw.node_id == "s1":
                pass

            self.sw.ports[port_num].init_port_graph_state()

        # Initialize port graph state per table and add its node to switch port graph
        for flow_table in self.sw.flow_tables:
            flow_table.init_port_graph_state()
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

    def init_switch_admitted_traffic(self):

        print "Computing Transfer Function for switch:", self.sw.node_id

        # Inject wildcard traffic at each ingress port of the switch's non-host ports
        for port in self.sw.non_host_port_iter():

            egress_node = self.get_egress_node(self.sw.node_id, port.port_number)
            dst_traffic_at_succ = Traffic(init_wildcard=True)
            end_to_end_modified_edges = []
            self.propagate_admitted_traffic(egress_node, dst_traffic_at_succ, None, egress_node,
                                            end_to_end_modified_edges)

        # Inject wildcard traffic at each ingress port of the switch
        for port in self.sw.host_port_iter():

            egress_node = self.get_egress_node(self.sw.node_id, port.port_number)

            dst_traffic_at_succ = Traffic(init_wildcard=True)
            dst_traffic_at_succ.set_field("ethernet_destination", int(port.attached_host.mac_addr.replace(":", ""), 16))
            end_to_end_modified_edges = []
            self.propagate_admitted_traffic(egress_node, dst_traffic_at_succ, None, egress_node,
                                            end_to_end_modified_edges)

    def compute_edge_admitted_traffic(self, traffic_to_propagate, edge):

        pred_admitted_traffic = Traffic()

        for ed in edge.edge_data_list:

            if edge.edge_type == "egress":

                # if the output_action type is applied, no written modifications take effect.
                if ed.edge_action.instruction_type == "applied":
                    traffic_to_propagate.set_written_modifications_apply(False)
                else:
                    traffic_to_propagate.set_written_modifications_apply(True)

            # Always roll-back applied modifications if the edge has any...
            if ed.applied_modifications:
                ttp = traffic_to_propagate.get_orig_traffic(ed.applied_modifications)
            else:
                ttp = traffic_to_propagate

            # At ingress edges, first roll-back any accumulated written modifications
            if edge.edge_type == "ingress":
                ttp = ttp.get_orig_traffic(use_embedded_written_modifications=True)

            i = ed.edge_filter_traffic.intersect(ttp)
            i.set_enabling_edge_data(ed)

            if not i.is_empty():
                # At all the non-ingress edges accumulate written modifications
                if edge.edge_type != "ingress" and ed.written_modifications:
                    i.set_written_modifications(ed.written_modifications)

                pred_admitted_traffic.union(i)

        return pred_admitted_traffic

    def update_admitted_traffic_due_to_port_state_change(self, port_num, event_type):

        end_to_end_modified_edges = []

        egress_node = self.get_egress_node(self.sw.node_id, port_num)

        # This will keep track of all the edges due to flow tables that were modified due to port event
        # This assumes that ports are always successors on these edges.
        all_modified_flow_table_edges = []

        # First the egress node causes bunch of changes
        for pred in self.predecessors_iter(egress_node):

            edge = self.get_edge(pred, egress_node)
            flow_table = pred.parent_obj

            # First get the modified edges in this flow_table (edges added/deleted/modified)
            modified_flow_table_edges = flow_table.update_port_graph_edges()

            self.modify_flow_table_edges(flow_table, modified_flow_table_edges)

            self.update_admitted_traffic(modified_flow_table_edges, end_to_end_modified_edges)

            all_modified_flow_table_edges.extend(modified_flow_table_edges)

        # Take care of the ingress node which holds the traffic that can get from here to others nodes
        ingress_node = self.get_ingress_node(self.sw.node_id, port_num)
        ingress_node_succ = self.sw.flow_tables[0].port_graph_node
        ingress_node_succ_edge = self.get_edge(ingress_node, ingress_node_succ)

        for other_port in self.sw.ports:

            dst = self.get_egress_node(self.sw.node_id, other_port)

            dst_traffic_at_succ = Traffic()
            if event_type == "port_down":
                pass
            elif event_type == "port_up":
                dst_traffic_at_succ = self.get_admitted_traffic(ingress_node_succ, dst)
            else:
                raise Exception("Unknown event")

            ingress_node_traffic = self.compute_edge_admitted_traffic(dst_traffic_at_succ, ingress_node_succ_edge)
            self.propagate_admitted_traffic(ingress_node, ingress_node_traffic, ingress_node_succ, dst,
                                            end_to_end_modified_edges)

        return end_to_end_modified_edges
