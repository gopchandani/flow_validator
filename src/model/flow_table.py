__author__ = 'Rakesh Kumar'


class Flow():
    def __init__(self, flow):
        self.priority = flow["flow"]["priority"]
        self.match = flow["flow"]["match"]
        self.actions = flow["flow"]["actions"]

    def passes_flow(self, src, dst, src_port, dst_port):
        pass


class FlowTable():
    def __init__(self, switch_flows):
        self.node_id = switch_flows["node"]["id"]
        self.node_type = switch_flows["node"]["type"]
        self.flow_list = []

        for f in switch_flows["flowStatistic"]:
            self.flow_list.append(Flow(f))

    def passes_flow(self, src, dst, src_port, dst_port):

        for flow in self.flow_list:
            print flow

        return True
