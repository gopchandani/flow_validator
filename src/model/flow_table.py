__author__ = 'Rakesh Kumar'

from collections import defaultdict

from port_graph_node import PortGraphNode
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
        self.written_actions = []
        self.applied_actions = []
        self.go_to_table = None

        self.instruction_set = None

        if self.sw.network_graph.controller == "odl":
            self.table_id = self.flow_json["table_id"]
            self.priority = int(self.flow_json["priority"])
            self.match = Match(match_json=self.flow_json["match"], controller="odl", flow=self)
            self.instruction_set = InstructionSet(self.sw, self, self.flow_json["instructions"]["instruction"])

        elif self.sw.network_graph.controller == "ryu":
            self.table_id = self.flow_json["table_id"]
            self.priority = int(self.flow_json["priority"])
            self.match = Match(match_json=self.flow_json["match"], controller="ryu", flow=self)
            self.instruction_set = InstructionSet(self.sw, self, self.flow_json["instructions"])

        elif self.sw.network_graph.controller == "sel":
            self.table_id = self.flow_json["tableId"]
            self.priority = int(self.flow_json["priority"])
            self.match = Match(match_json=self.flow_json["match"], controller="sel", flow=self)
            self.instruction_set = InstructionSet(self.sw, self, self.flow_json["instructions"])


        self.traffic_element = TrafficElement(init_match=self.match)
        self.traffic = Traffic()
        self.complement_traffic = Traffic()
        self.applied_traffic = None

        self.traffic.add_traffic_elements([self.traffic_element])
        self.complement_traffic.add_traffic_elements(self.traffic_element.get_complement_traffic_elements())


    def get_port_graph_edges(self, port_graph_edges):

        if self.instruction_set:

            # Prepare the raw material for edges

            self.instruction_set.populate_action_sets_for_port_graph_edges()

            self.applied_modifications = \
                self.instruction_set.applied_action_set.get_modified_fields_dict(self.traffic_element)

            self.written_modifications = \
                self.instruction_set.written_action_set.get_modified_fields_dict(self.traffic_element)

            self.applied_port_graph_edges = self.instruction_set.applied_action_set.get_action_set_port_graph_edges()

            self.written_port_graph_edges = self.instruction_set.written_action_set.get_action_set_port_graph_edges()

            self.goto_table_port_graph_edge = None

            if self.instruction_set.goto_table:

                if self.instruction_set.goto_table < len(self.sw.flow_tables):

                    self.goto_table_port_graph_edge = (self.sw.flow_tables[self.table_id].port_graph_node,
                                                       self.sw.flow_tables[self.instruction_set.goto_table].port_graph_node)
                else:
                    print "At switch:", self.sw.node_id, ", couldn't find flow table goto:", self.instruction_set.goto_table


            for out_port, output_action in self.applied_port_graph_edges:

                output_action.instruction_type = "applied"
                egress_node = self.sw.port_graph.get_egress_node(self.sw.node_id, out_port)

                port_graph_edges[egress_node].append((self.applied_traffic,
                                                           output_action,
                                                           self.applied_modifications,
                                                           self.written_modifications,
                                                           output_action.vuln_rank))

            for out_port, output_action in self.written_port_graph_edges:

                output_action.instruction_type = "written"
                egress_node = self.sw.port_graph.get_egress_node(self.sw.node_id, out_port)

                port_graph_edges[egress_node].append((self.applied_traffic,
                                                           output_action,
                                                           self.applied_modifications,
                                                           self.written_modifications,
                                                           output_action.vuln_rank))

            if self.goto_table_port_graph_edge:

                port_graph_edges[self.goto_table_port_graph_edge[1]].append((self.applied_traffic,
                                                                                  None,
                                                                                  self.applied_modifications,
                                                                                  self.written_modifications,
                                                                                  0))

        else:
            print "Assuming this means to drop."


class FlowTable():
    def __init__(self, sw, table_id, flow_list):

        self.sw = sw
        self.network_graph = sw.network_graph
        self.table_id = table_id
        self.flows = []

        self.port_graph_node = PortGraphNode(self.sw,
                                             self.sw.port_graph.get_table_node_id(self.sw.node_id, self.table_id),
                                             "table")

        self.port_graph_node.parent_obj = self

        # Edges from this table's node to port egress nodes and other tables' nodes are stored in this dictionary
        # The key is the succ node, and the list contains edge contents

        self.port_graph_edges = None

        for f in flow_list:
            f = Flow(sw, f)
            self.flows.append(f)

        #  Sort the flows list by priority
        self.flows = sorted(self.flows, key=lambda flow: flow.priority, reverse=True)


    def _get_port_graph_edges_dict(self):
        port_graph_edges = defaultdict(list)

        #print "flow_table:", self.table_id

        remaining_traffic = Traffic(init_wildcard=True)

        for flow in self.flows:

            #print "flow:", flow.flow_json

            intersection = flow.traffic.intersect(remaining_traffic)

            if not intersection.is_empty():

                # See what is left after this rule is through
                remaining_traffic = flow.complement_traffic.intersect(remaining_traffic)
                flow.applied_traffic = intersection

                flow.get_port_graph_edges(port_graph_edges)

            else:
                # Say that this flow does not matter
                flow.applied_traffic = None

        return port_graph_edges

    def compute_flow_table_port_graph_edges(self):

        self.port_graph_edges = self._get_port_graph_edges_dict()


    def update_port_graph_edges(self):

        modified_edges = []

        # Compute what these edges would look like now.
        new_port_graph_edges = self._get_port_graph_edges_dict()


        # Compare where the differences are return the edges that got affected
        # This ought to be a three prong comparison
        # 1. The edges that existed previously and now don;t
        # 2. The edges that did not exist previously but now do.
        # 3. The eges that existted previously and now do as well, but the contents of traffic filters/modifications
        # have changed


        return modified_edges

    def de_init_flow_table_port_graph(self):
        pass