__author__ = 'Rakesh Kumar'


import pprint

from netaddr import IPNetwork
from netaddr import IPAddress


class Flow():
    def __init__(self, flow):
        self.priority = flow["priority"]
        self.match = flow["match"]
        self.actions = flow["instructions"]["instruction"][0]["apply-actions"]["action"]

        print "Added Flow -- Priority:", self.priority, "Match:", self.match, "Actions:", self.actions

    def does_it_match(self, arriving_port, src, dst):
        ret_val = False
        src_ip = IPAddress(src)
        dst_ip = IPAddress(dst)

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

            elif match_field == 'ethernet-match':
                #TODO
                ret_val = True

            elif match_field == 'in-port':
                #TODO
                if self.match[match_field] != arriving_port:
                    ret_val = False

        return ret_val

    def does_it_forward(self, departure_port):
        ret_val = False

        # Requiring that a single action matches
        # TODO: Confirm with Ahmad the story of multiple actions here.

        for action in self.actions:
            if "output-action" in action:
                if action["output-action"]["output-node-connector"] == departure_port:
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
    def __init__(self, table_id, flow_list):

        self.table_id = table_id
        self.flow_list = []

        for f in flow_list:
            self.flow_list.append(Flow(f))

    def passes_flow(self, arriving_port, src, dst, departure_port):
        ret_val = False

        for flow in self.flow_list:
            ret_val = flow.passes_flow(arriving_port, src, dst, departure_port)

            # As soon as an admitting rule is found, stop looking further
            if ret_val:
                break

        return ret_val
