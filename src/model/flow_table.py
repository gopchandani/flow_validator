__author__ = 'Rakesh Kumar'


class Flow():
    def __init__(self, flow):
        self.priority = flow["flow"]["priority"]
        self.match = flow["flow"]["match"]
        self.actions = flow["flow"]["actions"]

        # pprint.pprint(self.match)
        # pprint.pprint(self.actions)
        # pprint.pprint(self.priority)


class FlowTable():
    def __init__(self, switch_flows):
        self.node_id = switch_flows["node"]["id"]
        self.node_type = switch_flows["node"]["type"]
        self.flow_list = []
        #
        # print self.node_id
        # print self.node_type

        for f in switch_flows["flowStatistic"]:
            self.flow_list.append(Flow(f))

