__author__ = 'Rakesh Kumar'

from collections import defaultdict

from action_set import ActionSet
from match import Match
from port import Port


class Switch():

    def __init__(self, sw_id, model):

        self.node_id = sw_id
        self.model = model
        self.flow_tables = []
        self.group_table = None
        self.ports = None

        #Synthesis stuff
        self.intents = defaultdict(dict)
        self.synthesis_tag = int(self.node_id.split(":")[1])

        #Analysis stuff
        self.in_port_match = None

        self.accepted_destination_match = {}

    def transfer_function(self, in_port_match):

        written_action_set = ActionSet(self)

        # Check if the switch has at least one table
        table_id_to_check = 0
        has_table_to_check = True
        next_table_matches_on = in_port_match

        while has_table_to_check:

            # Grab the table

            flow_table = self.flow_tables[table_id_to_check]

            # Get the highest priority matching flow in this table
            hpm_flow, intersection = flow_table.get_highest_priority_matching_flow(next_table_matches_on)

            if hpm_flow:

                # See if there were any apply-action instructions, if so, compute the resulting match
                # otherwise following along the same match to next table
                if hpm_flow.applied_actions:
                    table_applied_action_set = ActionSet(self)
                    table_applied_action_set.add_actions(hpm_flow.applied_actions, intersection)
                    next_table_matches_on = table_applied_action_set.get_resulting_match(next_table_matches_on)
                    written_action_set.add_actions(hpm_flow.applied_actions, intersection)
                else:
                    next_table_matches_on = in_port_match

                # If there are any written-actions that hpm_flow does, accumulate them
                if hpm_flow.written_actions:
                    written_action_set.add_actions(hpm_flow.written_actions, intersection)

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

        out_port_match = written_action_set.get_out_port_matches(in_port_match)

        return out_port_match

    def transfer_function_3(self, in_port_match):

        out_port_match = {}
        return out_port_match

    def compute_switch_port_graph(self):
        print "At Switch:", self.node_id

        # Add a node per physical port in port graph
        for port in self.ports:
            self.model.port_graph.add_port(self.ports[port])

        # Add a node per table in the port graph
        for flow_table in self.flow_tables:

            print "At Table:", flow_table.table_id

            # Add a output node in port graph for each table

            p = Port(self,
                     port_type = "table",
                     port_id = self.model.port_graph.get_table_port_id(self.node_id, flow_table.table_id))

            self.model.port_graph.g.add_node(p.port_id, p=p)
            flow_table.port = p

        for flow_table in self.flow_tables:

            # Try passing a wildcard through the flow table
            in_port_match = Match(init_wildcard=True)
            flow_table.compute_applied_matches_and_actions(in_port_match)
