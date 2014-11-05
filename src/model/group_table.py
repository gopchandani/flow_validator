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

    def does_output_action_forward(self, in_port, out_port):

        ret_val = False

        if self.out_port == out_port:
            ret_val = True

        elif self.out_port == "4294967288" and in_port == out_port:
            ret_val = True

        elif self.out_port == "4294967292":
            ret_val = True

        return ret_val

    def does_group_action_forward(self, in_port, out_port):

        ret_val = False

        #  Go through the groups that we have seen so far at this switch
        for group in self.group_table:
    
            if group["group-type"] == "group-all" and action["group-action"]["group-id"] == group["group-id"]:
    
                #  Check the bucket actions and see if any of them would do the trick
                for action_bucket in group["buckets"]["bucket"]:
                    ret_val = self.does_action_bucket_forward(action_bucket, in_port, out_port)
    
                    #  No need to keep going
                    if ret_val:
                        break
    
            # Check to see if there is a matching group_id of fast-failover type group is present...
            elif group["group-type"] == "group-ff" and action["group-action"]["group-id"] == group["group-id"]:
    
                #  Check the bucket actions and see if any of them would do the trick
                for action_bucket in group["buckets"]["bucket"]:
                    ret_val = self.does_action_bucket_forward(action_bucket, in_port, out_port)
    
                    #  No need to keep going
                    if ret_val:
                        break

        return ret_val

    def does_it_forward(self, in_port, out_port):
        ret_val = False

        if self.action_type == "output":
            ret_val = self.does_output_action_forward(in_port, out_port)

        elif self.action_type == "group":
            ret_val = self.does_group_action_forward(in_port, out_port)

        return ret_val

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

    def __init__(self, groups_json):

        self.group_list = []

        for group_json in groups_json:
            self.group_list.append(Group(group_json))


    def does_group_table_forward(self):
        pass