__author__ = 'Rakesh Kumar'

import pprint

class Action():

    def __init__(self, sw, action_json):

        self.sw = sw
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
        for group in self.sw.group_table.group_list:

            if group.group_type == "group-all" and group.group_id == self.group_id:
    
                #  Check the bucket actions and see if any of them would do the trick
                for action_bucket in group.bucket_list:
                    ret_val = action_bucket.does_it_forward(in_port, out_port)
                    if ret_val:
                        break
    
            # Check to see if there is a matching group_id of fast-failover type group is present...
            elif group.group_type == "group-ff" and group.group_id == self.group_id:
    
                #  Check the bucket actions and see if any of them would do the trick
                for action_bucket in group.bucket_list:
                    ret_val = action_bucket.does_it_forward(in_port, out_port)
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
    def __init__(self, sw, bucket_json):

        self.sw = sw
        self.action_list = []

        for action_json in bucket_json["action"]:
            self.action_list.append(Action(sw, action_json))

        self.bucket_id = bucket_json["bucket-id"]

        if "watch_port" in bucket_json:
            self.watch_port = bucket_json["watch_port"]

        if "weight" in bucket_json:
            self.weight = bucket_json["weight"]

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

        pprint.pprint(group_json)



class GroupTable():

    def __init__(self, sw, groups_json):

        self.sw = sw
        self.group_list = []

        for group_json in groups_json:
            self.group_list.append(Group(sw, group_json))


    def does_group_table_forward(self):
        pass