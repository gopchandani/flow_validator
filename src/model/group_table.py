__author__ = 'Rakesh Kumar'

from action_set import Action

import pprint

class Bucket():
    def __init__(self, sw, bucket_json):

        self.sw = sw
        self.action_list = []

        for action_json in bucket_json["action"]:
            self.action_list.append(Action(sw, action_json))

        #  Sort the action_list by order
        self.action_list = sorted(self.action_list, key=lambda action: action.order)

        self.bucket_id = bucket_json["bucket-id"]

        if "watch_port" in bucket_json:
            self.watch_port = str(bucket_json["watch_port"])

        if "weight" in bucket_json:
            self.weight = str(bucket_json["weight"])

    def does_it_forward(self, in_port, out_port):

        ret_val = False

        for action in self.action_list:
            ret_val = action.does_it_forward(in_port, out_port)
            if ret_val:
                break

        return ret_val

class Group():
    '''
    As per OF1.3 specification:

    A switch is not required to support all group types, just those marked "Required" below.

    The controller can also query the switch about which of the "Optional" group type it supports.
    Required: all:      Execute all buckets in the group. This group is used for multi-cast or broadcast forwarding.
                        The packet is effectively cloned for each bucket; one packet is processed for each bucket of the
                        group. If a bucket directs a packet explicitly out the ingress port, this packet clone is dropped.
                        If the controller writer wants to forward out the ingress port, the group should include an extra
                        bucket which includes an output action to the OFPP_IN_PORT reserved port.
    Optional: select:   Execute one bucket in the group. Packets are processed by a single bucket in the group,
                        based on a switch-computed selection algorithm (e.g. hash on some user-configured tuple or
                        simple round robin). All configuration and state for the selection algorithm is external to
                        OpenFlow. The selection algorithm should implement equal load sharing and can optionally be
                        based on bucket weights. When a port specified in a bucket in a select group goes down,
                        the switch may restrict bucket selection to the remaining set (those with forwarding actions
                        to live ports) instead of dropping packets destined to that port. This behavior may reduce
                        the disruption of a downed link or switch.

    Required: indirect: Execute the one defined bucket in this group. This group supports only a single bucket.
                        Allows multiple flow entries or groups to point to a common group identifier, supporting
                        faster, more efficient convergence.

    Optional: ff:       Execute the first live bucket. Each action bucket is associated with a specific port and/or
                        group that controls its liveness. The buckets are evaluated in the order defined by the group,
                        and the first bucket which is associated with a live port/group is selected. This group type
                        enables the switch to change forwarding without requiring a round trip to the controller.
                        If no buckets are live, packets are dropped.
    '''

    def __init__(self, sw, group_json):

        self.sw = sw
        self.barrier = group_json["barrier"]
        self.group_id = group_json["group-id"]
        self.group_type = group_json["group-type"]
        self.bucket_list = []

        for bucket_json in group_json["buckets"]["bucket"]:
            self.bucket_list.append(Bucket(sw, bucket_json))

        #  Sort the bucket_list by bucket-id
        self.bucket_list = sorted(self.bucket_list, key=lambda bucket: bucket.bucket_id)

    def get_active_action_list(self):
        active_action_list = []

        # If it is a _all_ group, collect all buckets
        if self.group_type == "group-all":

            for action_bucket in self.bucket_list:
                active_action_list.extend(action_bucket.action_list)

        # If it is a fast-failover group, collect the bucket which is active
        elif self.group_type == "group-ff":

            for action_bucket in self.bucket_list:

                # Check if the port that the bucket watches is actually up
                if self.sw.ports[action_bucket.watch_port].state == "up":
                    active_action_list.extend(action_bucket.action_list)
                    break

        return active_action_list

class GroupTable():

    def __init__(self, sw, groups_json):

        self.sw = sw
        self.groups = {}

        for group_json in groups_json:
            self.groups[group_json["group-id"]] = Group(sw, group_json)

