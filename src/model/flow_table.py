__author__ = 'Rakesh Kumar'


class Flow():
    def __init__(self, flow):
        self.priority = flow["flow"]["priority"]
        self.match = flow["flow"]["match"]
        self.actions = flow["flow"]["actions"]

class FlowTable():
    def __init__(self, switch_flows):
        self.node_id = switch_flows["node"]["id"]
        self.node_type = switch_flows["node"]["type"]
        self.flow_list = []

        for f in switch_flows["flowStatistic"]:
            self.flow_list.append(Flow(f))

    def passes_flow(self, src, dst, next_node_id):
        print "Checking passage:", self.node_id, "->", next_node_id

        return True
