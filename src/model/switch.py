__author__ = 'Rakesh Kumar'



class Switch():

    def __init__(self, sw_id):

        self.switch_id = sw_id
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