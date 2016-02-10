#!/usr/bin/env python3
# Copyright (c) 2015 Schweitzer Engineering Laboratories, Inc.

from __future__ import absolute_import
import ConfigTree
import OperationalTree
import Session

# session = Session.Http("http://davibuehpc2.ad.selinc.com:1234/")
session = Session.Http(u"http://selcontroller:1234/")

## Uncomment for extra debug info
#session.print_status = True
#session.print_data = True

session.auth_user_callback()
nodeOpTree = OperationalTree.nodesHttpAccess(session)
nodeConfTree = ConfigTree.nodesHttpAccess(session)
# linksOpTree = OperationalTree.linksHttpAccess(session)
# flowStatsOpTree = OperationalTree.flowStatsHttpAccess(session)
# flows = ConfigTree.flowsHttpAccess(session)



print u"There are {0} nodes in the operational tree".format(len(nodeOpTree.read_collection()))

for entry in nodeOpTree.read_collection():
    print u"==>{0}".format(entry.to_json())


print u"\nThere are {0} nodes in the config tree".format(len(nodeConfTree.read_collection()))

for entry in nodeConfTree.read_collection():
    print u"**>{0}".format(entry.to_json())

# def example_read_all():
# 	[x for x in flowStatsOpTree.read_collection()]

	
# def program_flow():
# 	flow = ConfigTree.Flow()
# 	instruction = ConfigTree.WriteActions()

# 	action = ConfigTree.OutputAction()
# 	action.out_port = 1
# 	action.action_type = "Output"

# 	instruction.actions.append(action)
# 	instruction.instruction_type = "WriteActions"

# 	flow.instructions.append(instruction)
# 	flow.node = "aca67a17567444349b60c189773286b5f"
# 	flow.match.in_port = "2"
# 	flow.enabled = True

# 	result = flows.create_single(flow)
