# Copyright (c) 2015 Schweitzer Engineering Laboratories, Inc.

import sys

import ConfigTree
import OperationalTree
import Session


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

    for idx, flow_config_tree in enumerate(flows_config_tree.read_collection()):
        if idx > 0:
            print("\n")
        print("Config Tree flow {0}\n{1}".format(idx, flow_config_tree.to_json()))

    print('='*50)

    flows_op_tree = OperationalTree.flowStatsHttpAccess(session)

    print("There are {0} flows in the operational tree".format(
        len(flows_op_tree.read_collection())))

    for idx, flow_op_tree in enumerate(flows_op_tree.read_collection()):
        if idx > 0:
            print("\n")
        print("Operational Tree flow {0}\n{1}".format(idx, flow_op_tree.to_json()))

if __name__ == '__main__':

    if len(sys.argv) != 2:
        print('Give me the controller URI! (e.g. http://davibuehpc2.ad.selinc.com:1234/)')

    else:
        main(sys.argv[1])
