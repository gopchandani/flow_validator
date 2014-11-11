__author__ = 'Rakesh Kumar'


from collections import defaultdict

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
        for group_id in self.sw.group_table.groups:
            group = self.sw.group_table.groups[group_id]

            if group.group_type == "group-all" and group.group_id == self.group_id:

                #  Check the bucket actions and see if any of them would do the trick in group-all case
                for action_bucket in group.bucket_list:
                    ret_val = action_bucket.does_it_forward(in_port, out_port)
                    if ret_val:
                        break

            # Check to see if there is a matching group_id of fast-failover type group is present...
            elif group.group_type == "group-ff" and group.group_id == self.group_id:

                #  Check the bucket actions and see if any of them would do the trick
                #  along with the condition that the watch_port of the bucket has to be up

                for action_bucket in group.bucket_list:

                    # Check if the port that the bucket watches is actually up
                    if self.sw.ports[action_bucket.watch_port].state == "up":
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


class ActionSet():

    def __init__(self, sw):

        # Modelling the ActionSet as a dictionary of lists, keyed by various actions.
        # These actions may be tucked away inside a group too and the type might be group

        self.action_set = defaultdict(list)

        self.sw = sw

    def add_actions(self, action_list):

        for action in action_list:

            if action.action_type == "group":
                if action.group_id in self.sw.group_table.groups:
                    group_active_action_list =  self.sw.group_table.groups[action.group_id].get_active_action_list()
                    self.add_actions(group_active_action_list)
            else:
                self.action_set[action.action_type].append(action)


    def get_out_ports(self):
        out_ports = []

        for action in self.action_set["output"]:
            out_ports.append(action.out_port)

        print out_ports

        return out_ports