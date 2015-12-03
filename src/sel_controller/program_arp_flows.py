#!/usr/bin/env python3
# Copyright (c) 2015 Schweitzer Engineering Laboratories, Inc.

import sys
import ConfigTree
import OperationalTree
import Session
# import requests

def config_port_2_operational_port(config_port, op_tree_ports):
    op_port_id = config_port.linked_key
    op_port = op_tree_ports.read_single(op_port_id)

    return op_port

def config_node_is_openflow(session, config_node):
    is_openflow = False

    op_id = config_node.linked_key

    op_node = OperationalTree.nodesHttpAccess(session).read_single(op_id)

    # print("{0}".format(op_node.to_json()))

    if op_node._odata_type == '#Sel.Sel5056.TopologyManager.Nodes.OpenFlowNode':
        is_openflow = True

    return is_openflow

def op_tree_node_id_2_config_tree_id(config_tree_nodes, op_tree_id):
    '''
    Find the op_tree_id in the config tree's linked_key field and return the
    config tree's id
    '''
    config_tree_id = None

    for config_tree_entry in config_tree_nodes.read_collection():
        if config_tree_entry.linked_key == op_tree_id:
            config_tree_id = config_tree_entry.id
            break

    return config_tree_id


def op_node_2_op_ports(op_node, op_tree_ports):

    op_ports = []

    for op_port in op_tree_ports.read_collection():
        if op_port.parent_node == op_node.id:
            op_ports.append( op_port )

    return op_ports

# def port_belongs_to_node(port, node):
#     port.parent_node == node.id

# def config_port_belongs_to_config_node(config_port, config_node):
#     return config_port.linked_key == config_node.

# def config_node_2_port_ids(config_node, config_tree_ports, op_tree_ports):
#     config_ports_linked_keys = []

#     for config_tree_port in config_tree_ports:
#         if config_tree_port.
    

def delete_group(group_id, config_tree_groups):
    id = ""
    for group in config_tree_groups.read_collection():
        if group.group_id == group_id:
            id = group.id
            break

    if len(id) > 0:
        print( "Deleting group with id {0}".format(id))
        config_tree_groups.delete_single(id)

def arp_flow(op_node, group_id, op_tree_ports, config_tree_nodes, config_tree_groups):
    '''
    ARP flow for the given node in the operational tree (op_node)

    Note: no loop-breaking is implemented, so if there are loops in the
    network you'll cause an ARP storm!
    '''

    group_id = 3  # Make this a parameter for this method?

    op_ports = op_node_2_op_ports(op_node, op_tree_ports)

    print("Found ports for node {0}".format(op_node.id))
    for port in op_ports:
        print("  {0}".format(port.id))

    buckets = []

    # For each port, create an output action on that port and a bucket
    for port in op_ports:
        action = ConfigTree.OutputAction()
        action.out_port = port.port_id
        action.action_type = ConfigTree.OfpActionType.output()
        action.max_length = 65535

        bucket = ConfigTree.Bucket()
        bucket.actions.append(action)
        bucket.watch_port = 4294967295
        bucket.watch_group = 4294967295

        buckets.append(bucket)

    # TODO: Create a Group and add all of the buckets to it
    #       Note: *I* assign the group.group_id to an (int) ID that is
    #       not in use on the system

    group = ConfigTree.Group()
    config_tree_node_id = op_tree_node_id_2_config_tree_id(config_tree_nodes, op_node.id)
    group.node = config_tree_node_id
    group.group_id = group_id
    group.buckets = buckets # Append each one instead?
    group.group_type = ConfigTree.OfpGroupType.all()

    # Write the Group to the REST interface (to get an ID)

    group_created = config_tree_groups.create_single(group)

    # print("group_created:\n{0}".format(group_created.to_json()))

    # Create a GroupAction (set the Group's id to the group.id)

    group_action = ConfigTree.GroupAction()

    group_action.group_id = group_id

    # TODO: ?? Create an instruction (a WriteAction?) and append the
    #       GroupAction to its actions list?

    instruction = ConfigTree.WriteActions()
    instruction.actions.append(group_action)
    instruction.instruction_type = ConfigTree.OfpInstructionType.write_actions()

    # TODO: Create the flow, append the instruction to the instructions

    flow = ConfigTree.Flow()
    flow.instructions.append(instruction)
    flow.node = config_tree_node_id
    flow.match.eth_type = "2054"                  # ARP
    # # Priority needs to be above 0!
    flow.priority = 1
    flow.enabled = True
    
    return flow

def test_config_port_2_operational_port(session):
    config_tree_ports = ConfigTree.portsHttpAccess(session).read_collection()
    op_tree_ports = OperationalTree.portsHttpAccess(session)

    for config_tree_port in config_tree_ports:
        op_port = config_port_2_operational_port(config_tree_port, op_tree_ports)
        print("Port: Config: {0}, Operational: {1}".format(config_tree_port.id, op_port.id))
    

def main(uri):
    print("Got uri = {0}".format(uri))
    session = Session.Http(uri)

    ## Uncomment for extra debug info
    # session.print_status = True
    # session.print_data = True

    session.auth_user_callback()

    ## test_config_port_2_operational_port(session)

    my_group_id = 3

    # Delete the group in case it's already in place...
    config_tree_groups = ConfigTree.groupsHttpAccess(session)
    delete_group(my_group_id, config_tree_groups)

    op_tree_ports = OperationalTree.portsHttpAccess(session)
    op_tree_nodes = OperationalTree.nodesHttpAccess(session)
    op_node = op_tree_nodes.read_single('OpenFlow:1') # Pass in 'OpenFlow:1'?
    config_tree_nodes = ConfigTree.nodesHttpAccess(session)

    flow = arp_flow(op_node, my_group_id, op_tree_ports, config_tree_nodes, config_tree_groups)
    
    print("main() - flow:\n{0}".format(flow.to_json()))

    response = ConfigTree.flowsHttpAccess(session).create_single(flow)

    print("Flow Creation Response:\n{0}".format(response.to_json()))

if __name__ == '__main__':

    if len(sys.argv) != 2:
        print('Give me the controller URI' + \
              ' (e.g. http://davibuehpc2.ad.selinc.com:1234/)')
    else:
        main(sys.argv[1])
