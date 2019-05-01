from collections import defaultdict
from rpc import flow_validator_pb2

from netaddr import IPNetwork


class SDNSimClient(object):

    def __init__(self, nc):
        super(SDNSimClient, self).__init__()

        self.nc = nc
        self.rpc_links = defaultdict(dict)

        links = nc.get_all_links()
        for src_node in links:
            for src_node_port in links[src_node]:
                dst_list = links[src_node][src_node_port]
                dst_node = dst_list[0]
                dst_node_port = dst_list[1]

                rpc_link = flow_validator_pb2.Link(src_node=src_node,
                                                   src_port_num=int(src_node_port),
                                                   dst_node=dst_node,
                                                   dst_port_num=int(dst_node_port))

                self.rpc_links[src_node][dst_node] = rpc_link

    def prepare_rpc_actions(self, actions):
        rpc_actions = []

        for action in actions:

            rpc_action = flow_validator_pb2.Action(type=action["type"])

            if action["type"] == "SET_FIELD" and "field" in action and "value" in action:
                rpc_action.modified_field = action["field"]
                rpc_action.modified_value = int(action["value"])

            if action["type"] == "GROUP" and "group_id" in action:
                rpc_action.group_id = int(action["group_id"])

            if action["type"] == "OUTPUT" and "port" in action:
                rpc_action.output_port_num = action["port"]

            rpc_actions.append(rpc_action)

        return rpc_actions

    def prepare_rpc_field_value(self, field_name, field_value):
        field_val = None
        has_vlan_tag = False

        if field_name == "in_port":
            try:
                field_val = int(field_value)
            except ValueError:
                parsed_in_port = field_value.split(":")[2]
                field_val = int(parsed_in_port)

        elif field_name == "eth_type":
            field_val = int(field_value)

        elif field_name == "eth_src":
            mac_int = int(field_value.replace(":", ""), 16)
            field_val = mac_int

        elif field_name == "eth_dst":
            mac_int = int(field_value.replace(":", ""), 16)
            field_val = mac_int

        # TODO: Add graceful handling of IP addresses
        elif field_name == "nw_src":
            field_val = IPNetwork(field_value)
        elif field_name == "nw_dst":
            field_val = IPNetwork(field_value)

        elif field_name == "ip_proto":
            field_val = int(field_value)
        elif field_name == "tcp_dst":

            if field_value == 6:
                field_val = int(field_value)
            else:
                field_val = sys.maxsize

        elif field_name == "tcp_src":

            if field_value == 6:
                field_val = int(field_value)
            else:
                field_val = sys.maxsize

        elif field_name == "udp_dst":

            if field_value == 17:
                field_val = int(field_value)
            else:
                field_val = sys.maxsize

        elif field_name == "udp_src":

            if field_value == 17:
                field_val = int(field_value)
            else:
                field_val = sys.maxsize

        elif field_name == "vlan_vid":

            if field_value == "0x1000/0x1000":
                field_val = 0x1000
            else:
                field_val = 0x1000 + int(field_value)

        if not isinstance(field_val, IPNetwork):
            return flow_validator_pb2.FlowRuleMatchFieldVal(value_start=field_val, value_end=field_val)
        else:
            return flow_validator_pb2.FlowRuleMatchFieldVal(value_start=field_val.first, value_end=field_val.last)

    def prepare_rpc_match(self, match):

        match_fields = {}
        for field_name, field_value in match.items():
            match_fields[field_name] = self.prepare_rpc_field_value(field_name, field_value)

        return match_fields

    def prepare_rpc_instructions(self, instructions):
        rpc_instructions = []

        for instruction in instructions:

            if instruction["type"] == "GOTO_TABLE":
                rpc_instruction = flow_validator_pb2.Instruction(
                    type=instruction["type"],
                    go_to_table_num=instruction["table_id"])
            else:
                rpc_instruction = flow_validator_pb2.Instruction(
                    type=instruction["type"],
                    actions=self.prepare_rpc_actions(instruction["actions"]))

            rpc_instructions.append(rpc_instruction)

        return rpc_instructions

    def prepare_rpc_switches(self):
        switches = self.nc.get_switches()

        rpc_switches = []

        for sw_id, switch in switches.items():

            rpc_ports = []
            for port in switch["ports"]:

                try:
                    port_no = int(port["port_no"])
                except:
                    continue

                rpc_port = flow_validator_pb2.Port(port_num=port_no, hw_addr=port["hw_addr"])
                rpc_ports.append(rpc_port)

            rpc_groups = []
            for group in switch["groups"]:

                rpc_buckets = []
                for bucket in group["buckets"]:
                    rpc_actions = self.prepare_rpc_actions(bucket["actions"])
                    rpc_bucket = flow_validator_pb2.Bucket(watch_port_num=bucket["watch_port"],
                                                           weight=bucket["weight"],
                                                           actions=rpc_actions)
                    rpc_buckets.append(rpc_bucket)

                rpc_group = flow_validator_pb2.Group(id=group["group_id"], type=group["type"], buckets=rpc_buckets)
                rpc_groups.append(rpc_group)

            rpc_flow_tables = []
            for table_num, flow_table in switch["flow_tables"].items():

                rpc_flow_rules = []
                for flow_rule in flow_table:
                    rpc_flow_rule = flow_validator_pb2.FlowRule(
                        priority=int(flow_rule["priority"]),
                        flow_rule_match=self.prepare_rpc_match(flow_rule["match"]),
                        instructions=self.prepare_rpc_instructions(flow_rule["instructions"]))

                    rpc_flow_rules.append(rpc_flow_rule)

                rpc_flow_table = flow_validator_pb2.FlowTable(table_num=int(table_num), flow_rules=rpc_flow_rules)
                rpc_flow_tables.append(rpc_flow_table)

            rpc_switch = flow_validator_pb2.Switch(flow_tables = rpc_flow_tables,
                                                   group_table=rpc_groups,
                                                   ports=rpc_ports,
                                                   switch_id='s' + str(sw_id))

            rpc_switches.append(rpc_switch)

        return rpc_switches

    def prepare_rpc_hosts(self):
        hosts = self.nc.get_host_nodes()

        rpc_hosts = []

        for host_switch in hosts.values():
            for host in host_switch:
                rpc_host = flow_validator_pb2.Host(host_IP=host["host_IP"],
                                                   host_MAC=host["host_MAC"],
                                                   host_name=host["host_name"],
                                                   host_switch_id=host["host_switch_id"])
                rpc_hosts.append(rpc_host)

        return rpc_hosts

    def prepare_rpc_link(self, src_node, dst_node):

        src_node_port = 0
        dst_node_port = 0

        rpc_link = flow_validator_pb2.Link(src_node=src_node,
                                           src_port_num=int(src_node_port),
                                           dst_node=dst_node,
                                           dst_port_num=int(dst_node_port))

        return rpc_link

    def prepare_rpc_links(self):
        rpc_links_list = []

        for src_node in self.rpc_links:
            for dst_node in self.rpc_links[src_node]:
                rpc_links_list.append(self.rpc_links[src_node][dst_node])

        return rpc_links_list

    def prepare_rpc_network_graph(self):

        rpc_switches = self.prepare_rpc_switches()
        rpc_hosts = self.prepare_rpc_hosts()
        rpc_links = self.prepare_rpc_links()

        rpc_ng = flow_validator_pb2.NetworkGraph(controller="grpc",
                                                 switches=rpc_switches, hosts=rpc_hosts, links=rpc_links)

        return rpc_ng
