#!/usr/bin/env python3
# Copyright (c) 2015 Schweitzer Engineering Laboratories, Inc.

import sys
import ConfigTree
# import OperationalTree
import Session
# import requests

# Config tree entry's id value
# switch1_config_id = "a1126f3aae2994672bfc1470a4ad499e5"
# switch2_config_id = "afa65e228525a481bbc778c7f54e9ef3e"

switch1_op_id = "OpenFlow:1"
switch1_config_id = None

host1_mac = "00:00:00:AA:AA:00"
host2_mac = "00:00:00:AA:AB:00"

broadcast_mac = "ff:ff:ff:ff:ff:ff"

host1_ip = "10.0.0.2"
host2_ip = "10.0.0.3"

def op_tree_node_id_2_config_tree_id(session, op_tree_id):
    '''
    Find the op_tree_id in the config tree's linked_key field and return the
    config tree's id
    '''
    config_tree_nodes = ConfigTree.nodesHttpAccess(session).read_collection()

    config_tree_id = None

    for config_tree_entry in config_tree_nodes:
        if config_tree_entry.linked_key == op_tree_id:
            config_tree_id = config_tree_entry.id
            break

    return config_tree_id

def host1_to_host2_all():
    action = ConfigTree.OutputAction()
    action.out_port = 2
    # Possible values for action_type are found in the class OfpActionType
    # in ConfigTree.py
    action.action_type = "Output"
    action.max_length = 65535  # 65535 means "all of the packet"

    instruction = ConfigTree.WriteActions()
    instruction.actions.append(action)
    # Possible values for instruction_type are found in the class
    # OfpInstructionType in ConfigTree.py
    instruction.instruction_type = "WriteActions"

    flow = ConfigTree.Flow()
    flow.instructions.append(instruction)
    flow.node = switch1_config_id
    flow.match.in_port = "1"
    # Priority needs to be above 0 to avoid the catch-all we put in for host
    # discovery
    flow.priority = 1
    flow.enabled = True

    print(switch1_config_id)

    return flow

def host2_to_host1_all():
    action = ConfigTree.OutputAction()
    action.out_port = 1
    # Possible values for action_type are found in the class OfpActionType
    # in ConfigTree.py
    action.action_type = "Output"
    action.max_length = 65535  # 65535 means "all of the packet"

    instruction = ConfigTree.WriteActions()
    instruction.actions.append(action)
    # Possible values for instruction_type are found in the class
    # OfpInstructionType in ConfigTree.py
    instruction.instruction_type = "WriteActions"

    flow = ConfigTree.Flow()
    flow.instructions.append(instruction)
    flow.node = switch1_config_id
    flow.match.in_port = "2"
    flow.priority = 1
    flow.enabled = True

    return flow

def host1_to_host2_arp():
    action = ConfigTree.OutputAction()
    action.out_port = 2
    # Possible values for action_type are found in the class OfpActionType
    # in ConfigTree.py
    action.action_type = "Output"
    action.max_length = 65535  # 65535 means "all of the packet"

    instruction = ConfigTree.WriteActions()
    instruction.actions.append(action)
    # Possible values for instruction_type are found in the class
    # OfpInstructionType in ConfigTree.py
    instruction.instruction_type = "WriteActions"

    flow = ConfigTree.Flow()
    flow.instructions.append(instruction)
    flow.node = switch1_config_id
    flow.match.in_port = "1"
    flow.match.eth_src = host1_mac
    flow.match.eth_type = "2054"                  # ARP
    # Priority needs to be above 0!
    flow.priority = 1
    flow.enabled = True

    return flow

def host2_to_host1_arp():
    action = ConfigTree.OutputAction()
    action.out_port = 1
    # Possible values for action_type are found in the class OfpActionType
    # in ConfigTree.py
    action.action_type = "Output"
    action.max_length = 65535  # 65535 means "all of the packet"

    instruction = ConfigTree.WriteActions()
    instruction.actions.append(action)
    # Possible values for instruction_type are found in the class
    # OfpInstructionType in ConfigTree.py
    instruction.instruction_type = "WriteActions"

    flow = ConfigTree.Flow()
    flow.instructions.append(instruction)
    flow.node = switch1_config_id
    flow.match.in_port = "2"
    flow.match.eth_src = host2_mac
    flow.match.eth_type = "2054"                  # ARP
    # Priority needs to be above 0!
    flow.priority = 1
    flow.enabled = True

    return flow

def host1_to_host2_icmp():
    action = ConfigTree.OutputAction()
    action.out_port = 2
    # Possible values for action_type are found in the class OfpActionType
    # in ConfigTree.py
    action.action_type = "Output"
    action.max_length = 65535  # 65535 means "all of the packet"

    instruction = ConfigTree.WriteActions()
    instruction.actions.append(action)
    # Possible values for instruction_type are found in the class
    # OfpInstructionType in ConfigTree.py
    instruction.instruction_type = "WriteActions"

    flow = ConfigTree.Flow()
    flow.instructions.append(instruction)
    flow.node = switch1_config_id
    flow.match.in_port = "1"
    # flow.match.eth_dst = host2_mac     # Destination host's MAC
    # flow.match.ipv4_src = host1_ip
    # flow.match.ipv4_dst = host2_ip
    flow.match.eth_type = "2048"                  # IPv4
    flow.match.ip_proto = "1"                     # ICMP
    # Priority needs to be above 0!
    flow.priority = 1
    flow.enabled = True

    return flow

def host2_to_host1_icmp():
    action = ConfigTree.OutputAction()
    action.out_port = 1
    # Possible values for action_type are found in the class OfpActionType
    # in ConfigTree.py
    action.action_type = "Output"
    action.max_length = 65535  # 65535 means "all of the packet"

    instruction = ConfigTree.WriteActions()
    instruction.actions.append(action)
    # Possible values for instruction_type are found in the class
    # OfpInstructionType in ConfigTree.py
    instruction.instruction_type = "WriteActions"

    flow = ConfigTree.Flow()
    flow.instructions.append(instruction)
    flow.node = switch1_config_id
    flow.match.in_port = "2"
    # flow.match.eth_dst = host2_mac     # Destination host's MAC
    # flow.match.ipv4_src = host2_ip
    # flow.match.ipv4_dst = host1_ip
    flow.match.eth_type = "2048"                  # IPv4
    flow.match.ip_proto = "1"                     # ICMP
    flow.priority = 1
    flow.enabled = True

    return flow

def main(uri):
    print("Got uri = {0}".format(uri))
    session = Session.Http(uri)

    ## Uncomment for extra debug info
    # session.print_status = True
    # session.print_data = True

    session.auth_user_callback()

    global switch1_config_id
    switch1_config_id = op_tree_node_id_2_config_tree_id(session, switch1_op_id)
    print("switch1_config_id = {0}".format(switch1_config_id))

    flows_config_tree = ConfigTree.flowsHttpAccess(session)

    print("There are {0} flows in the config tree".format(
        len(flows_config_tree.read_collection())))

    #
    # This is the simple rule pair of all traffic in port 1 goes out port 2
    # and all traffic in port 2 goes out port 1...
    #

    # flow_path = [ host1_to_host2_all(),
    #               host2_to_host1_all() ]

    #
    # These are pairs of rules to just allow arp and icmp to and from the two
    # hosts...
    #

    flow_path = [ host1_to_host2_arp(),
                  host2_to_host1_arp(),
                  host1_to_host2_icmp(),
                  host2_to_host1_icmp()]

    for each_flow in flow_path:
        # result is a Flow... doesn't help much with errors
        result = flows_config_tree.create_single(each_flow)

if __name__ == '__main__':

    if len(sys.argv) != 2:
        print('Give me the controller URI' + \
              ' (e.g. http://davibuehpc2.ad.selinc.com:1234/)')
    else:
        main(sys.argv[1])
