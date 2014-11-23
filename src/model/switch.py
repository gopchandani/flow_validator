__author__ = 'Rakesh Kumar'

from collections import defaultdict

from action import ActionSet


class Switch():

    synthesis_tag = 1

    def __init__(self, sw_id, model):

        self.node_id = sw_id
        self.model = model
        self.flow_tables = None
        self.group_table = None
        self.ports = None

        #Synthesis stuff
        self.intents = defaultdict(dict)

        self.synthesis_tag = Switch.synthesis_tag
        Switch.synthesis_tag += 1

        self.synthesis_tag = int(self.node_id.split(":")[1])

        #Analysis stuff
        self.in_port_match = None
        self.discovered = False



    def passes_flow(self, flow_match, out_port):

        is_reachable = False

        for flow_table_id in self.flow_tables:
            node_flow_table = self.flow_tables[flow_table_id]

            #  Will this flow_table do the trick?
            is_reachable = node_flow_table.passes_flow(flow_match, out_port)

            # If flow table passes, just break, otherwise keep going to the next table
            if is_reachable:
                break

        return is_reachable

    def transfer_function(self, in_port_match):

        action_set = ActionSet(self)
        out_ports = []

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

                # If there are any written-actions that hpm_flow does, accumulate them
                if hpm_flow.written_actions:
                    action_set.add_actions(hpm_flow.written_actions, intersection)

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

                # TODO: Send match data and action set to the next table
                # TODO: Right now all tables are matching on the same arriving match
                next_table_matches_on = in_port_match

            else:
                has_table_to_check = False

        out_port_match = action_set.get_out_port_matches(in_port_match)

        return out_port_match
