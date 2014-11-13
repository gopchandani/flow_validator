__author__ = 'Rakesh Kumar'

from action import ActionSet

class Switch():

    def __init__(self, sw_id, model):

        self.switch_id = sw_id
        self.model = model
        self.flow_tables = None
        self.group_table = None
        self.ports = None

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

    def get_out_ports(self, flow_match):

        action_set = ActionSet(self)
        out_ports = []

        # Check if the switch has at least one table
        table_id_to_check = 0
        has_table_to_check = table_id_to_check in self.flow_tables

        while has_table_to_check:

            # Grab the table
            flow_table = self.flow_tables[table_id_to_check]

            # Get the highest priority matching flow in this table
            hpm_flow = flow_table.get_highest_priority_matching_flow(flow_match)

            # TODO: Go through the instructions in hpm_flow and accumulat any output actions
            if hpm_flow:
                action_set.add_actions(hpm_flow.actions)

                # TODO: See if the hpm_flow has any go-to-next table instructions, if so
                # update table_id_to_check and has_table_to_check accordingly
                table_id_to_check = None
                has_table_to_check = False

                # TODO: Send match data and action set to the next table

        out_ports = action_set.get_out_ports(flow_match.in_port)

        return out_ports

    def get_out_port_match_flows(self, flow_match):
        pass