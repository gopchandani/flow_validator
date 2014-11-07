__author__ = 'Rakesh Kumar'


import pprint

from netaddr import IPNetwork
from netaddr import IPAddress

from group_table import Action


class Flow():
    def __init__(self, sw, flow):

        self.sw = sw
        self.priority = int(flow["priority"])
        self.match = flow["match"]
        self.actions = []
        apply_actions_json = flow["instructions"]["instruction"][0]["apply-actions"]

        for action_json in apply_actions_json["action"]:
            self.actions.append(Action(sw, action_json))

        #print "-- Added flow with priority:", self.priority, "match:", flow["match"], "actions: ", self.actions

    def does_it_match(self, flow_match):
        ret_val = False
        src_ip = IPAddress(flow_match.src_ip_addr)
        dst_ip = IPAddress(flow_match.dst_ip_addr)

        # Match on every field
        for match_field in self.match:

            if match_field == 'ipv4-destination':
                nw_dst = IPNetwork(self.match[match_field])
                ret_val = dst_ip in nw_dst
                if not ret_val:
                    break

            elif match_field == 'ipv4-source':
                nw_src = IPNetwork(self.match[match_field])
                ret_val = src_ip in nw_src
                if not ret_val:
                    break

            elif match_field == 'in-port':
                ret_val = (self.match[match_field] == flow_match.in_port)

        return ret_val

    def does_it_forward(self, in_port, out_port):
        ret_val = False

        # Requiring that any single action has to forward it
        for action in self.actions:
            if action.does_it_forward(in_port, out_port):
                ret_val = True
                break

        return ret_val

    def passes_flow(self, flow_match, out_port):
        ret_val = False
        if self.does_it_match(flow_match):
            if self.does_it_forward(flow_match.in_port, out_port):
                ret_val = True

        return ret_val

class FlowTable():
    def __init__(self, sw, table_id, flow_list):

        self.sw = sw
        self.table_id = table_id
        self.flows = []

        for f in flow_list:
            f = Flow(sw, f)
            self.flows.append(f)

        #  Sort the flows list by priority
        self.flows = sorted(self.flows, key=lambda flow: flow.priority, reverse=True)

    def passes_flow(self, flow_match, out_port):
        ret_val = False
        for flow in self.flows:
            ret_val = flow.passes_flow(flow_match, out_port)

            # As soon as an admitting rule is found, stop looking further
            if ret_val:
                break

        return ret_val
