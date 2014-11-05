__author__ = 'Rakesh Kumar'


import pprint

from netaddr import IPNetwork
from netaddr import IPAddress

from group_table import Action


class Flow():
    def __init__(self, flow, group_table):
        self.priority = flow["priority"]
        self.match = flow["match"]
        self.actions = []
        apply_actions_json = flow["instructions"]["instruction"][0]["apply-actions"]

        for action_json in apply_actions_json["action"]:
            self.actions.append(Action(action_json))

        self.group_table = group_table

        #print "-- Added flow with priority:", self.priority, "match:", flow["match"], "actions: ", self.actions

    def does_it_match(self, in_port, src, dst):
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

            elif match_field == 'in-port':
                ret_val = (self.match[match_field] == in_port)

        return ret_val


    def does_action_bucket_forward(self, action_bucket, in_port, out_port):
        
        ret_val = False
        
        for bucket_action in action_bucket["action"]:
            ret_val = bucket_action.does_output_action_forward(bucket_action["output-action"], in_port, out_port)
            if ret_val:
                break

        return ret_val

    def does_it_forward(self, in_port, out_port):
        ret_val = False

        # Requiring that any single action has to forward it
        for action in self.actions:
            if action.does_it_forward(in_port, out_port):
                ret_val = True
                break

        return ret_val

    def passes_flow(self, in_port, src, dst, out_port):
        ret_val = False
        if self.does_it_match(in_port, src, dst):
            if self.does_it_forward(in_port, out_port):
                ret_val = True

        return ret_val

class FlowTable():
    def __init__(self, table_id, flow_list, group_list):

        self.table_id = table_id
        self.flow_list = []
        self.group_list = group_list

        for f in flow_list:
            self.flow_list.append(Flow(f, group_list))

    def passes_flow(self, in_port, src, dst, out_port):
        ret_val = False

        for flow in self.flow_list:
            ret_val = flow.passes_flow(in_port, src, dst, out_port)

            # As soon as an admitting rule is found, stop looking further
            if ret_val:
                break

        return ret_val
