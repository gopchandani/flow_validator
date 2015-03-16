__author__ = 'Rakesh Kumar'

from collections import defaultdict

from action_set import ActionSet
from traffic import Traffic
from port import Port


class Switch():

    def __init__(self, sw_id, network_graph):

        self.node_id = sw_id
        self.network_graph = network_graph
        self.flow_tables = []
        self.group_table = None
        self.ports = None

        #Synthesis stuff
        self.intents = defaultdict(dict)
        self.synthesis_tag = int(self.node_id.split(":")[1])

        #Analysis stuff
        self.in_port_match = None
        self.accepted_destination_match = {}

        self.port_graph = None

    def transfer_function(self, in_port_match, in_port):

        written_action_set = ActionSet(self)

        # Check if the switch has at least one table
        table_id_to_check = 0
        has_table_to_check = True
        next_table_matches_on = in_port_match

        while has_table_to_check:

            # Grab the table
            flow_table = self.flow_tables[table_id_to_check]

            #print "At Table: ", flow_table.table_id


            # Get the highest priority matching flow in this table
            hpm_flow, intersection = flow_table.get_highest_priority_matching_flow(next_table_matches_on)

            if hpm_flow:

                # See if there were any apply-action instructions, if so, compute the resulting match
                # otherwise following along the same match to next table
                if hpm_flow.applied_actions:
                    table_applied_action_set = ActionSet(self)
                    table_applied_action_set.add_active_actions(hpm_flow.applied_actions, intersection)
                    next_table_matches_on = table_applied_action_set.get_resulting_match_element(next_table_matches_on)

                    #Ugly
                    written_action_set.add_active_actions(hpm_flow.applied_actions, intersection)
                else:
                    next_table_matches_on = in_port_match

                # If there are any written-actions that hpm_flow does, accumulate them
                if hpm_flow.written_actions:
                    written_action_set.add_active_actions(hpm_flow.written_actions, intersection)

                # if the hpm_flow has any go-to-next table instructions then
                # update table_id_to_check and has_table_to_check accordingly
                if hpm_flow.go_to_table:
                    table_id_to_check = hpm_flow.go_to_table
                    has_table_to_check = True
                else:
                    has_table_to_check = False

                # TODO: Handle the cases for other instructions, e.g. meta information

            else:
                has_table_to_check = False

        out_port_match = written_action_set.get_out_port_matches(in_port_match, in_port)

        return out_port_match

    def prepare_switch_port_graph(self, port_graph):

        self.port_graph = port_graph

        # Add a node per table in the port graph
        for flow_table in self.flow_tables:

            # Add a output node in port graph for each table
            p = Port(self,
                     port_type="table",
                     port_id=self.port_graph.get_table_port_id(self.node_id, flow_table.table_id))

            self.port_graph.g.add_node(p.port_id, p=p)
            flow_table.port = p
            flow_table.port_graph = self.port_graph

        # Add two nodes per physical port in port graph one for incoming and outgoing direction
        # Connect incoming direction port to table 0's port
        for port in self.ports:

            in_p = Port(self,
                        port_type="ingress",
                        port_id=self.port_graph.get_incoming_port_id(self.node_id, port))

            out_p = Port(self,
                         port_type="egress",
                         port_id=self.port_graph.get_outgoing_port_id(self.node_id, port))

            in_p.port_number = int(port)
            out_p.port_number = int(port)

            self.port_graph.add_port(in_p)
            self.port_graph.add_port(out_p)

            incoming_port_match = Traffic(init_wildcard=True)
            incoming_port_match.set_field("in_port", int(port))

            # None of this happens if there are no flow tables
            if self.flow_tables:

                self.port_graph.add_edge(in_p,
                                               self.flow_tables[0].port, (None, None),
                                               incoming_port_match)
            else:
                print "No flow tables in switch:", self.node_id


        # Find out what else can happen when traffic comes to this switch.
        for flow_table in self.flow_tables:

            # Try passing a wildcard through the flow table
            flow_table.compute_applied_matches_and_actions()

