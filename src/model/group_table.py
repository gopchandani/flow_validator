__author__ = 'Rakesh Kumar'

import pprint

class Action():
    def __init__(self, action_json):
        self.order = action_json["order"]
        self.action_type = None

        if "output-action" in action_json:
            self.action_type = "output"
            self.out_port = action_json["output-action"]["output-node-connector"]

        if "group-action" in action_json:
            self.action_type = "group"
            self.group_id = action_json["group-action"]["group-id"]


class Bucket():
    def __init__(self, bucket_json):
        self.action_list = []
        for action_json in bucket_json["action"]:
            self.action_list.append(Action(action_json))

        self.bucket_id = bucket_json["bucket-id"]

        if "watch_port" in bucket_json:
            self.watch_port = bucket_json["watch_port"]

        if "weight" in bucket_json:
            self.weight = bucket_json["weight"]


class Group():
    def __init__(self, group_json):

        self.barrier = group_json["barrier"]
        self.group_id = group_json["group-id"]
        self.group_type = group_json["group-type"]
        self.bucket_list = []

        for bucket_json in group_json["buckets"]["bucket"]:
            self.bucket_list.append(Bucket(bucket_json))


        pprint.pprint(group_json)



class GroupTable():
    def __init__(self, group_list):
        pass