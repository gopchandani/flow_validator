from . import ConfigTree
from . import OperationalTree
from . import Session

session = Session.Http("http://selcontroller:1234/")

## Uncomment for extra debug info
session.print_status = True
session.print_data = True

session.auth_user_callback(user="hobbs", role="Engineer")
opNodes = OperationalTree.nodesHttpAccess(session)
confNodes = ConfigTree.nodesHttpAccess(session)
opLinks = OperationalTree.linksHttpAccess(session)
flowStats = OperationalTree.flowStatsHttpAccess(session)
flows = ConfigTree.flowsHttpAccess(session)

print(flows)


def example_read_all():
    [x for x in flowStats.read_collection()]


def program_flow():
    node = confNodes.read_collection()[0]
    node_id = node.id

    flow = ConfigTree.Flow()

    action = ConfigTree.OutputAction()
    action.out_port = 1
    action.action_type = "Output"
    action.max_length = 65535

    instruction = ConfigTree.WriteActions()
    instruction.actions.append(action)
    instruction.instruction_type = "WriteActions"

    flow.instructions.append(instruction)
    flow.node = node_id
    flow.buffer_id = 0
    flow.cookie = 0
    flow.priority = 1
    flow.table_id = 0

    # enumerating these isnt required just added for reference
    flow.match.in_port = "3"
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

	
program_flow()