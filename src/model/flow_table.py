__author__ = 'Rakesh Kumar'

from edge_data import EdgeData
from match import Match
from traffic import Traffic, TrafficElement
from instruction_set import InstructionSet

class Flow():

    def __hash__(self):
        return hash(str(self.sw.node_id) + str(self.table_id) + str(id(self)))

    def __init__(self, sw, flow_json):

        self.sw = sw
        self.flow_json = flow_json
        self.network_graph = sw.network_graph
        self.port_graph = None
        self.written_actions = []
        self.applied_actions = []
        self.go_to_table = None

        if self.sw.network_graph.controller == "odl":
            self.table_id = self.flow_json["table_id"]
            self.priority = int(self.flow_json["priority"])
            self.match = Match(match_json=self.flow_json["match"], controller="odl", flow=self)
        
        elif self.sw.network_graph.controller == "ryu":
            self.table_id = self.flow_json["table_id"]
            self.priority = int(self.flow_json["priority"])
            self.match = Match(match_json=self.flow_json["match"], controller="ryu", flow=self)

        self.port_graph_edges = []
        self.traffic_element = TrafficElement(init_match=self.match)
        self.traffic = Traffic()
        self.complement_traffic = Traffic()
        self.applied_traffic = None

        self.traffic.add_traffic_elements([self.traffic_element])
        self.complement_traffic.add_traffic_elements(self.traffic_element.get_complement_traffic_elements())

    def add_port_graph_edges(self):

        if not "instructions" in self.flow_json:
            print "Assuming this means to drop."
        else:
            if self.sw.network_graph.controller == "odl":
                self.instruction_set = InstructionSet(self.sw, self, self.flow_json["instructions"]["instruction"])

            elif self.sw.network_graph.controller == "ryu":
                self.instruction_set = InstructionSet(self.sw, self, self.flow_json["instructions"])

            self.applied_modifications = \
                self.instruction_set.applied_action_set.get_modified_fields_dict(self.traffic_element)

            self.written_modifications = \
                self.instruction_set.written_action_set.get_modified_fields_dict(self.traffic_element)

            port_graph_edges = self.instruction_set.applied_action_set.get_port_graph_edges()

            for out_port, output_action in port_graph_edges:

                outgoing_port = self.port_graph.get_port(
                    self.port_graph.get_outgoing_port_id(self.sw.node_id, out_port))

                e = self.port_graph.add_edge(self.sw.flow_tables[self.table_id].port,
                                             outgoing_port,
                                             self,
                                             output_action,
                                             self.applied_traffic,
                                             self.applied_modifications,
                                             self.written_modifications)

                self.port_graph_edges.append(e)

            port_graph_edges = self.instruction_set.written_action_set.get_port_graph_edges()

            for out_port, output_action in port_graph_edges:

                outgoing_port = self.port_graph.get_port(
                    self.port_graph.get_outgoing_port_id(self.sw.node_id, out_port))

                e = self.port_graph.add_edge(self.sw.flow_tables[self.table_id].port,
                                             outgoing_port,
                                             self,
                                             output_action,
                                             self.applied_traffic,
                                             self.applied_modifications,
                                             self.written_modifications)

                self.port_graph_edges.append(e)

            # See the edge impact of any go-to-table instruction
            if self.instruction_set.goto_table:

                e = self.port_graph.add_edge(self.sw.flow_tables[self.table_id].port,
                                             self.sw.flow_tables[self.instruction_set.goto_table].port,
                                             self,
                                             None,
                                             self.applied_traffic,
                                             self.applied_modifications,
                                             self.written_modifications)

                self.port_graph_edges.append(e)

    def update_port_graph_edges(self):

        for src_port_id, dst_port_id, edge_action in self.port_graph_edges:

            if edge_action:
                if self.sw.port_graph.get_port(dst_port_id).state != "down":
                    edge_action.update_active_status()
                else:
                    edge_action.is_active = False

class FlowTable():
    def __init__(self, sw, table_id, flow_list):

        self.sw = sw
        self.network_graph = sw.network_graph
        self.table_id = table_id
        self.flows = []
        self.input_port = None
        self.port_graph = None

        for f in flow_list:
            f = Flow(sw, f)
            self.flows.append(f)

        #  Sort the flows list by priority
        self.flows = sorted(self.flows, key=lambda flow: flow.priority, reverse=True)

    def init_flow_table_port_graph(self):

        remaining_traffic = Traffic(init_wildcard=True)

        for flow in self.flows:

            intersection = flow.traffic.intersect(remaining_traffic)
            flow.port_graph = self.port_graph

            if not intersection.is_empty():

                # See what is left after this rule is through
                remaining_traffic = flow.complement_traffic.intersect(remaining_traffic)
                flow.applied_traffic = intersection

                # Add the edges in the portgraph
                flow.add_port_graph_edges()
            else:
                # Say that this flow does not matter
                flow.applied_traffic = None

    def de_init_flow_table_port_graph(self):
        pass