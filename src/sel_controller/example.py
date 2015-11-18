from __future__ import absolute_import
import ConfigTree
import OperationalTree
import Session

session = Session.Http(u"http://selcontroller:1234/")

## Uncomment for extra debug info
session.print_status = False
session.print_data = False

session.auth_user_callback(user=u"hobbs", role=u"Engineer")
opNodes = OperationalTree.nodesHttpAccess(session)
confNodes = ConfigTree.nodesHttpAccess(session)
opLinks = OperationalTree.linksHttpAccess(session)
flowStats = OperationalTree.flowStatsHttpAccess(session)
flows = ConfigTree.flowsHttpAccess(session)


def example_read_all():
    [x for x in flowStats.read_collection()]


def program_flow():
    node = confNodes.read_collection()[0]
    node_id = node.id

    flow = ConfigTree.Flow()

    action = ConfigTree.OutputAction()
    action.out_port = 1
    action.action_type = u"Output"
    action.max_length = 65535

    instruction = ConfigTree.WriteActions()
    instruction.actions.append(action)
    instruction.instruction_type = u"WriteActions"

    flow.instructions.append(instruction)
    flow.node = node_id
    flow.buffer_id = 0
    flow.cookie = 0
    flow.priority = 1
    flow.table_id = 0

    # enumerating these isnt required just added for reference
    flow.match.in_port = u"3"
    flow.eth_dst = None
    flow.eth_src = None
    flow.ipv4_dst = None
    flow.ipv4_src = None
    flow.eth_type = None
    flow.tcp_src = None
    flow.tcp_dst = None
    flow.udp_src = None
    flow.udp_dst = None
    flow.vlan_vid = None
    flow.vlan_pcp = None
    flow.ip_proto = None

    flow.enabled = True

    result = flows.create_single(flow)
    type(result)
    print(result)

	
program_flow()