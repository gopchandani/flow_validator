__author__ = 'Rakesh Kumar'

from collections import defaultdict

from action import ActionSet
from match import Match


class Switch():

    def __init__(self, sw_id, model):

        self.node_id = sw_id
        self.model = model
        self.flow_tables = None
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
        has_table_to_check = table_id_to_check in self.flow_tables
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
                    has_table_to_check = table_id_to_check in self.flow_tables

                    # Throw a tantrum if this check if False, switch is telling lies
                    if not has_table_to_check:
                        raise Exception("has_table_to_check should have been True")
                else:
                    has_table_to_check = False

                # TODO: Handle the cases for other instructions, e.g. meta information

            else:
                has_table_to_check = False

        out_port_match = written_action_set.get_out_port_matches(in_port_match)

        return out_port_match


    def transfer_function_2(self, in_port_match):


        for flow_table in self.flow_tables.values():

            print "At table:", flow_table.table_id

            # Get the highest priority matching flow in this table
            for matched_flow, intersection, complement in flow_table.get_next_matching_flow(in_port_match):
                print "Matched Flow:", matched_flow.applied_actions, matched_flow.written_actions, matched_flow.go_to_table
                print "Intersection:", intersection
                print "Complement:", complement


        out_port_match = {}
        return out_port_match


    def transfer_function_2(self, in_port_match):


        for flow_table in self.flow_tables.values():

            print "At table:", flow_table.table_id

            # Get the highest priority matching flow in this table
            for matched_flow, intersection, complement in flow_table.get_next_matching_flow(in_port_match):
                print "Matched Flow:", matched_flow.applied_actions, matched_flow.written_actions, matched_flow.go_to_table
                print "Intersection:", intersection
                print "Complement:", complement


        out_port_match = {}
        return out_port_match

    def transfer_function_3(self, in_port_match):

        for flow_table in self.flow_tables.values():

            print "At table:", flow_table.table_id
            print flow_table.get_all_rule_matches(in_port_match)

        out_port_match = {}
        return out_port_match
