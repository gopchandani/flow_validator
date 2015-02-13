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

