#!/usr/bin/env python3
# Copyright (c) 2015 Schweitzer Engineering Laboratories, Inc.

import sys

import ConfigTree
# import OperationalTree
import Session

# Unused
def is_empty_match(a_match):
    result = (a_match.__dict__ == ConfigTree.Match().__dict__)
    return result

def main(uri):
    session = Session.Http(uri)

    ## Uncomment for extra debug info
    #session.print_status = True
    #session.print_data = True

    session.auth_user_callback()

    # Config Tree Flows...

    flows_config_tree = ConfigTree.flowsHttpAccess(session)

    print("There are {0} flows in the config tree".format(
        len(flows_config_tree.read_collection())))

    for flow_config_tree in flows_config_tree.read_collection():
        flow_id = flow_config_tree.id
        print("Flow id: {0}".format(flow_id))
        flows_config_tree.delete_single(flow_id)

if __name__ == '__main__':

    if len(sys.argv) != 2:
        print('Give me the controller URI! (e.g. http://davibuehpc2.ad.selinc.com:1234/)')

    else:
        main(sys.argv[1])
