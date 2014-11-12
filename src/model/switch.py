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

        # Go through each FlowTable
        for flow_table_id in self.flow_tables:
            flow_table = self.flow_tables[flow_table_id]

            # Get highest priority matching flow entry
            hpm = flow_table.get_highest_priority_matching_flow(flow_match)
            if hpm:
                action_set.add_actions(hpm.actions)

            # TODO: Send match data and action set to the next table


        out_ports =  action_set.get_out_ports(flow_match.in_port)

        return out_ports