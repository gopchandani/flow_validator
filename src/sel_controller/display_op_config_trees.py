#!/usr/bin/env python3
# Copyright (c) 2015 Schweitzer Engineering Laboratories, Inc.

import sys

import ConfigTree
import OperationalTree
import Session


def main(uri):
    print("Got uri = {0}".format(uri))
    session = Session.Http(uri)

    ## Uncomment for extra debug info
    #session.print_status = True
    #session.print_data = True

    session.auth_user_callback()

    # Operational Tree Nodes...

    nodes_op_tree = OperationalTree.nodesHttpAccess(session)

    print("There are {0} nodes in the operational tree".format(
        len(nodes_op_tree.read_collection())
    ))

    for node_op_tree in nodes_op_tree.read_collection():
        print("==>{0}".format(node_op_tree.to_json()))

    # Config Tree Nodes...

    nodes_conf_tree = ConfigTree.nodesHttpAccess(session)

    print("\nThere are {0} nodes in the config tree".format(
        len(nodes_conf_tree.read_collection())
    ))

    for node_conf_tree in nodes_conf_tree.read_collection():
        print("**>{0}".format(node_conf_tree.to_json()))

    # Operational Tree Links...

    links_op_tree = OperationalTree.linksHttpAccess(session)

    print("\nThere are {0} links in the operational tree".format(
        len(links_op_tree.read_collection())
    ))

    for link_op_tree in links_op_tree.read_collection():
        print("[]>{0}".format(link_op_tree.to_json()))

if __name__ == '__main__':

    if len(sys.argv) != 2:
        print('Give me the controller URI! (e.g. http://davibuehpc2.ad.selinc.com:1234/)')

    else:
        main(sys.argv[1])
