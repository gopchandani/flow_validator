__author__ = 'Rakesh Kumar'

from netaddr import IPNetwork
from netaddr import IPAddress


class Flow():
    def __init__(self, flow):
        self.priority = flow["flow"]["priority"]
        self.match = flow["flow"]["match"]
        self.actions = flow["flow"]["actions"]

    def does_it_match(self, arriving_port, src, dst):
        ret_val = True
        src_ip = IPAddress(src)
        dst_ip = IPAddress(dst)

        # Match on every field
        for match_field in self.match['matchField']:

            if match_field['type'] == 'NW_DST':
                nw_dst = IPNetwork(match_field['value'] + '/' + match_field['mask'])
                ret_val = dst_ip in nw_dst
                if not ret_val:
                    break

            elif match_field['type'] == 'NW_SRC':
                nw_src = IPNetwork(match_field['value'] + '/' + match_field['mask'])
                ret_val = src_ip in nw_src
                if not ret_val:
                    break

        return ret_val

    def does_it_forward(self, departure_port):
        ret_val = False

        for action in self.actions:
            if action['type'] == 'OUTPUT' and action['port']['id'] == departure_port:
                ret_val = True
                break

        return ret_val

    def passes_flow(self, arriving_port, src, dst, departure_port):
        ret_val = False
        if self.does_it_match(arriving_port, src, dst):
            if self.does_it_forward(departure_port):
                ret_val = True
                print "Found a rule that will forward this."

        return ret_val


class FlowTable():
    def __init__(self, switch_flows):
        self.node_id = switch_flows["node"]["id"]
        self.node_type = switch_flows["node"]["type"]
        self.flow_list = []

        for f in switch_flows["flowStatistic"]:
            self.flow_list.append(Flow(f))

    def passes_flow(self, arriving_port, src, dst, departure_port):

        ret_val = False

        for flow in self.flow_list:
            ret_val = flow.passes_flow(arriving_port, src, dst, departure_port)

            # As soon as an admitting rule is found, stop looking further
            if ret_val:
                break

        return ret_val
