__author__ = 'Rakesh Kumar'


import pprint

from netaddr import IPNetwork
from netaddr import IPAddress


class Flow():
    def __init__(self, flow, group_list):
        self.priority = flow["priority"]
        self.match = flow["match"]
        self.actions = flow["instructions"]["instruction"][0]["apply-actions"]["action"]
        self.group_list = group_list

        #print "-- Added flow with priority:", self.priority, "match:", flow["match"], "actions: ", self.actions

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

            elif match_field == 'in-port':
                ret_val = (self.match[match_field] == arriving_port)

        return ret_val

    def does_it_forward(self, arriving_port, departure_port):
        ret_val = False

        # Requiring that a single action matches

        for action in self.actions:
            if "output-action" in action:
                if action["output-action"]["output-node-connector"] == departure_port:
                    ret_val = True
                    break

            if "group-action" in action:

                for bucket in self.group_list:

                    # Check to see if there is a matching group_id of fast-failover type group is present...
                    if bucket["group-type"] == "group-ff" and \
                                    action["group-action"]["group-id"] == bucket["group-id"]:

                        #  Check the bucket actions and see if any of them would do the trick
                        for bucket_actions in bucket["buckets"]["bucket"]:
                            for bucket_action in bucket_actions["action"]:
                                if bucket_action["output-action"]["output-node-connector"] == departure_port:
                                    ret_val = True
                                    break

                                #  If the output port is IN_PORT
                                if bucket_action["output-action"]["output-node-connector"] == "4294967288" \
                                        and arriving_port == departure_port:
                                    ret_val = True
                                    break

                            #  No need to keep going
                            if ret_val:
                                break

        return ret_val

    def passes_flow(self, arriving_port, src, dst, departure_port):
        ret_val = False
        if self.does_it_match(arriving_port, src, dst):
            if self.does_it_forward(arriving_port, departure_port):
                ret_val = True

        return ret_val


class FlowTable():
    def __init__(self, table_id, flow_list, group_list):

        self.table_id = table_id
        self.flow_list = []
        self.group_list = group_list

        for f in flow_list:
            self.flow_list.append(Flow(f, group_list))

    def passes_flow(self, arriving_port, src, dst, departure_port):
        ret_val = False

        for flow in self.flow_list:
            ret_val = flow.passes_flow(arriving_port, src, dst, departure_port)

            # As soon as an admitting rule is found, stop looking further
            if ret_val:
                break

        return ret_val
