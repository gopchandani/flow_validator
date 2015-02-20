__author__ = 'Rakesh Kumar'

from action_set import Action

import pprint

class Bucket():
    def __init__(self, sw, bucket_json):

        self.sw = sw
        self.action_list = []
        self.watch_port = None
        self.weight = None

        for action_json in bucket_json["action"]:
            self.action_list.append(Action(sw, action_json))

        #  Sort the action_list by order
        self.action_list = sorted(self.action_list, key=lambda action: action.order)
        self.bucket_id = bucket_json["bucket-id"]

        if "watch_port" in bucket_json:
            self.watch_port = str(bucket_json["watch_port"])

        if "weight" in bucket_json:
            self.weight = str(bucket_json["weight"])

    def is_live(self):

        # Check if the watch port is up.
        if self.watch_port:
             return self.sw.ports[self.watch_port].state == "up"

        # If no watch_port was specified, then assume the bucket is always live
        else:
            return True

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

    def get_all_action_list(self):

        all_action_list = []

        # If it is a _all_ group, collect all buckets
        if self.group_type == "group-all":

            for action_bucket in self.bucket_list:
                all_action_list.extend(action_bucket.action_list)

        # If it is a fast-failover group, collect the bucket which is active
        elif self.group_type == "group-ff":

            # at any point in time, only those actions are active that belong to the first live bucket

            # We begin by scanning the action buckets for the first live bucket, once found we break
            i = 0
            while i < len(self.bucket_list):
                this_bucket = self.bucket_list[i]
                if this_bucket.is_live():
                    all_action_list.extend(this_bucket.action_list)
                    i += 1
                    break
                else:
                    # Also adding any non-live buckets encountered until then to be as such
                    for action in this_bucket.action_list:
                        action.is_active = False
                    all_action_list.extend(this_bucket.action_list)
                    i += 1

            # If there are any buckets left, we add them as inactive buckets
            while i < len(self.bucket_list):
                this_bucket = self.bucket_list[i]
                for action in this_bucket.action_list:
                    action.is_active = False
                all_action_list.extend(this_bucket.action_list)
                i += 1

        return all_action_list

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
                if action_bucket.is_live():
                    active_action_list.extend(action_bucket.action_list)
                    break

        return active_action_list

class GroupTable():

    def __init__(self, sw, groups_json):

        self.sw = sw
        self.groups = {}

        for group_json in groups_json:
            self.groups[group_json["group-id"]] = Group(sw, group_json)

