# Copyright (c) 2015 Schweitzer Engineering Laboratories, Inc.
from __future__ import absolute_import
import datetime
import json
from sel_controller.Session import EntityAccess

#
# Containers and Entity Sets
#


class ErrorState(object):

    @staticmethod
    def in_progress():
        return u"InProgress"

    @staticmethod
    def failure():
        return u"Failure"

    @staticmethod
    def success():
        return u"Success"


class OfpActionType(object):

    @staticmethod
    def set_field():
        return u"SetField"

    @staticmethod
    def output():
        return u"Output"

    @staticmethod
    def dec_nw_ttl():
        return u"DecNwTtl"

    @staticmethod
    def push_vlan():
        return u"PushVlan"

    @staticmethod
    def experimenter():
        return u"Experimenter"

    @staticmethod
    def push_mpls():
        return u"PushMpls"

    @staticmethod
    def set_queue():
        return u"SetQueue"

    @staticmethod
    def group():
        return u"Group"

    @staticmethod
    def push_pbb():
        return u"PushPbb"

    @staticmethod
    def pop_pbb():
        return u"PopPbb"

    @staticmethod
    def set_nw_ttl():
        return u"SetNwTtl"

    @staticmethod
    def pop_mpls():
        return u"PopMpls"

    @staticmethod
    def dec_mpls_ttl():
        return u"DecMplsTtl"

    @staticmethod
    def copy_ttl_out():
        return u"CopyTtlOut"

    @staticmethod
    def set_mpls_ttl():
        return u"SetMplsTtl"

    @staticmethod
    def copy_ttl_in():
        return u"CopyTtlIn"

    @staticmethod
    def pop_vlan():
        return u"PopVlan"


class OfpInstructionType(object):

    @staticmethod
    def clear_actions():
        return u"ClearActions"

    @staticmethod
    def write_metadata():
        return u"WriteMetadata"

    @staticmethod
    def meter():
        return u"Meter"

    @staticmethod
    def goto_table():
        return u"GotoTable"

    @staticmethod
    def apply_actions():
        return u"ApplyActions"

    @staticmethod
    def write_actions():
        return u"WriteActions"

    @staticmethod
    def experimenter():
        return u"Experimenter"


class OfpPortStatus(object):

    @staticmethod
    def live():
        return u"Live"

    @staticmethod
    def link_down():
        return u"LinkDown"

    @staticmethod
    def link_up():
        return u"LinkUp"

    @staticmethod
    def blocked():
        return u"Blocked"


class OfpGroupType(object):

    @staticmethod
    def fast_failover():
        return u"FastFailover"

    @staticmethod
    def select():
        return u"Select"

    @staticmethod
    def indirect():
        return u"Indirect"

    @staticmethod
    def all():
        return u"All"


class DiscoveryTrustState(object):

    @staticmethod
    def certificate():
        return u"Certificate"

    @staticmethod
    def internal():
        return u"Internal"

    @staticmethod
    def untrusted():
        return u"Untrusted"

    @staticmethod
    def user():
        return u"User"


class OfpPortStatus(object):

    @staticmethod
    def live():
        return u"Live"

    @staticmethod
    def link_down():
        return u"LinkDown"

    @staticmethod
    def link_up():
        return u"LinkUp"

    @staticmethod
    def blocked():
        return u"Blocked"


class State(object):

    @staticmethod
    def adopted():
        return u"Adopted"

    @staticmethod
    def none():
        return u"None"

    @staticmethod
    def established():
        return u"Established"

    @staticmethod
    def unadopted():
        return u"Unadopted"

    @staticmethod
    def disconnected():
        return u"Disconnected"

    @staticmethod
    def configured():
        return u"Configured"


class DurationType(object):

    @staticmethod
    def momentary():
        return u"Momentary"

    @staticmethod
    def persistent():
        return u"Persistent"


class SeverityLevel(object):

    @staticmethod
    def notice():
        return u"Notice"

    @staticmethod
    def critical():
        return u"Critical"

    @staticmethod
    def error():
        return u"Error"

    @staticmethod
    def alert():
        return u"Alert"

    @staticmethod
    def debug():
        return u"Debug"

    @staticmethod
    def emergency():
        return u"Emergency"

    @staticmethod
    def informational():
        return u"Informational"

    @staticmethod
    def warning():
        return u"Warning"


class EventState(object):

    @staticmethod
    def raised():
        return u"Raised"

    @staticmethod
    def cleared():
        return u"Cleared"


# Container
# --OperationalTree


class NodesEntityAccess(EntityAccess):
    def __init__(self, session):
        super(NodesEntityAccess, self).__init__(session, u'default/operational/', Resolver())
        self.entity_base_name = u"nodes"
        self.entity_odata_type = u"#Sel.Sel5056.TopologyManager.Nodes.OperationalNode"

    def adopt(self, item):
        pyson_payload = {}
        item_id = item.id
        return self.execute_action(item_id, pyson_payload, u'Sel', u'Adopt')

    def adopt_with_config(self, item, config_key):
        pyson_payload = {}
        pyson_payload[u'configKey'] = config_key
        item_id = item.id
        return self.execute_action(item_id, pyson_payload, u'Sel', u'AdoptWithConfig')

    def unadopt(self, item):
        pyson_payload = {}
        item_id = item.id
        return self.execute_action(item_id, pyson_payload, u'Sel', u'Unadopt')

    def replace_config(self, item, config_key):
        pyson_payload = {}
        pyson_payload[u'configKey'] = config_key
        item_id = item.id
        return self.execute_action(item_id, pyson_payload, u'Sel', u'ReplaceConfig')


class PortsEntityAccess(EntityAccess):
    def __init__(self, session):
        super(PortsEntityAccess, self).__init__(session, u'default/operational/', Resolver())
        self.entity_base_name = u"ports"
        self.entity_odata_type = u"#Sel.Sel5056.TopologyManager.Ports.OperationalPort"

    def adopt(self, item):
        pyson_payload = {}
        item_id = item.id
        return self.execute_action(item_id, pyson_payload, u'Sel', u'Adopt')

    def adopt_with_config(self, item, config_key):
        pyson_payload = {}
        pyson_payload[u'configKey'] = config_key
        item_id = item.id
        return self.execute_action(item_id, pyson_payload, u'Sel', u'AdoptWithConfig')

    def unadopt(self, item):
        pyson_payload = {}
        item_id = item.id
        return self.execute_action(item_id, pyson_payload, u'Sel', u'Unadopt')

    def replace_config(self, item, config_key):
        pyson_payload = {}
        pyson_payload[u'configKey'] = config_key
        item_id = item.id
        return self.execute_action(item_id, pyson_payload, u'Sel', u'ReplaceConfig')


class LinksEntityAccess(EntityAccess):
    def __init__(self, session):
        super(LinksEntityAccess, self).__init__(session, u'default/operational/', Resolver())
        self.entity_base_name = u"links"
        self.entity_odata_type = u"#Sel.Sel5056.TopologyManager.Links.OperationalLink"

    def adopt(self, item):
        pyson_payload = {}
        item_id = item.id
        return self.execute_action(item_id, pyson_payload, u'Sel', u'Adopt')

    def adopt_with_config(self, item, config_key):
        pyson_payload = {}
        pyson_payload[u'configKey'] = config_key
        item_id = item.id
        return self.execute_action(item_id, pyson_payload, u'Sel', u'AdoptWithConfig')

    def unadopt(self, item):
        pyson_payload = {}
        item_id = item.id
        return self.execute_action(item_id, pyson_payload, u'Sel', u'Unadopt')

    def replace_config(self, item, config_key):
        pyson_payload = {}
        pyson_payload[u'configKey'] = config_key
        item_id = item.id
        return self.execute_action(item_id, pyson_payload, u'Sel', u'ReplaceConfig')


class EventsEntityAccess(EntityAccess):
    def __init__(self, session):
        super(EventsEntityAccess, self).__init__(session, u'default/operational/', Resolver())
        self.entity_base_name = u"events"
        self.entity_odata_type = u"#Sel.Sel5056.Common.DataBroker.Types.EventBus.Event"


class FlowStatsEntityAccess(EntityAccess):
    def __init__(self, session):
        super(FlowStatsEntityAccess, self).__init__(session, u'default/operational/', Resolver())
        self.entity_base_name = u"flowStats"
        self.entity_odata_type = u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.FlowStats"


class GroupDescEntityAccess(EntityAccess):
    def __init__(self, session):
        super(GroupDescEntityAccess, self).__init__(session, u'default/operational/', Resolver())
        self.entity_base_name = u"groupDesc"
        self.entity_odata_type = u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.GroupDesc"


class PortDescEntityAccess(EntityAccess):
    def __init__(self, session):
        super(PortDescEntityAccess, self).__init__(session, u'default/operational/', Resolver())
        self.entity_base_name = u"portDesc"
        self.entity_odata_type = u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.PortDesc"


class DeviceCapabilitiesEntityAccess(EntityAccess):
    def __init__(self, session):
        super(DeviceCapabilitiesEntityAccess, self).__init__(session, u'default/operational/', Resolver())
        self.entity_base_name = u"deviceCapabilities"
        self.entity_odata_type = u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.DeviceCapability"


class TableStatsEntityAccess(EntityAccess):
    def __init__(self, session):
        super(TableStatsEntityAccess, self).__init__(session, u'default/operational/', Resolver())
        self.entity_base_name = u"tableStats"
        self.entity_odata_type = u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.TableStats"


class PortStatsEntityAccess(EntityAccess):
    def __init__(self, session):
        super(PortStatsEntityAccess, self).__init__(session, u'default/operational/', Resolver())
        self.entity_base_name = u"portStats"
        self.entity_odata_type = u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.PortStats"


class TransactionsEntityAccess(EntityAccess):
    def __init__(self, session):
        super(TransactionsEntityAccess, self).__init__(session, u'default/operational/', Resolver())
        self.entity_base_name = u"transactions"
        self.entity_odata_type = u"#Sel.Sel5056.Common.RestBroker.Models.RestTransaction"

    def commit(self, item):
        pyson_payload = {}
        item_id = item.id
        return self.execute_action(item_id, pyson_payload, u'Sel', u'Commit')


class OxmTlv(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.MatchFields.OxmTlv'

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pass

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        pass

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class TypeKey(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.Common.DataBroker.Types.TypeKey'

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pass

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        pass

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class Action(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Action'
        self.action_type = u''
        self.set_order = 0

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'actionType'] = self.action_type
        pyson_object[u'setOrder'] = self.set_order

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'actionType' in pyson_object:
            self.action_type = pyson_object[u'actionType']
        if u'setOrder' in pyson_object:
            self.set_order = pyson_object[u'setOrder']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class Match(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Match'
        self.in_port = u''
        self.eth_dst = u''
        self.eth_src = u''
        self.ipv4_dst = u''
        self.ipv4_src = u''
        self.eth_type = u''
        self.tcp_src = u''
        self.tcp_dst = u''
        self.udp_src = u''
        self.udp_dst = u''
        self.vlan_vid = u''
        self.vlan_pcp = u''
        self.ip_proto = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'inPort'] = self.in_port
        pyson_object[u'ethDst'] = self.eth_dst
        pyson_object[u'ethSrc'] = self.eth_src
        pyson_object[u'ipv4Dst'] = self.ipv4_dst
        pyson_object[u'ipv4Src'] = self.ipv4_src
        pyson_object[u'ethType'] = self.eth_type
        pyson_object[u'tcpSrc'] = self.tcp_src
        pyson_object[u'tcpDst'] = self.tcp_dst
        pyson_object[u'udpSrc'] = self.udp_src
        pyson_object[u'udpDst'] = self.udp_dst
        pyson_object[u'vlanVid'] = self.vlan_vid
        pyson_object[u'vlanPcp'] = self.vlan_pcp
        pyson_object[u'ipProto'] = self.ip_proto

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'inPort' in pyson_object:
            self.in_port = pyson_object[u'inPort']
        if u'ethDst' in pyson_object:
            self.eth_dst = pyson_object[u'ethDst']
        if u'ethSrc' in pyson_object:
            self.eth_src = pyson_object[u'ethSrc']
        if u'ipv4Dst' in pyson_object:
            self.ipv4_dst = pyson_object[u'ipv4Dst']
        if u'ipv4Src' in pyson_object:
            self.ipv4_src = pyson_object[u'ipv4Src']
        if u'ethType' in pyson_object:
            self.eth_type = pyson_object[u'ethType']
        if u'tcpSrc' in pyson_object:
            self.tcp_src = pyson_object[u'tcpSrc']
        if u'tcpDst' in pyson_object:
            self.tcp_dst = pyson_object[u'tcpDst']
        if u'udpSrc' in pyson_object:
            self.udp_src = pyson_object[u'udpSrc']
        if u'udpDst' in pyson_object:
            self.udp_dst = pyson_object[u'udpDst']
        if u'vlanVid' in pyson_object:
            self.vlan_vid = pyson_object[u'vlanVid']
        if u'vlanPcp' in pyson_object:
            self.vlan_pcp = pyson_object[u'vlanPcp']
        if u'ipProto' in pyson_object:
            self.ip_proto = pyson_object[u'ipProto']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class Instruction(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Instruction'
        self.instruction_type = u''
        self.actions = []

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'instructionType'] = self.instruction_type
        # Complex Copy of actions
        actions_result = []
        for item_from_actions in self.actions:
            actions_result.append(item_from_actions.to_pyson())
        pyson_object[u'actions'] = actions_result

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'instructionType' in pyson_object:
            self.instruction_type = pyson_object[u'instructionType']
        if u'actions' in pyson_object:
            self.actions = []
            actions_json_list = pyson_object[u'actions']
            for actions_json_element in actions_json_list:
                actions_odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Action'
                if u'@odata.type' in actions_json_element:
                    actions_odata_type = actions_json_element[u'@odata.type']
                new_element = Resolver.get_new_object(actions_odata_type)
                new_element.from_pyson(actions_json_element)
                self.actions.append(new_element)

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class Port(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Port'
        self.advertised = 0
        self.config = 0
        self.curr = 0
        self.current_speed = 0
        self.hardware_address = u''
        self.max_speed = 0
        self.name = u''
        self.port_id = 0
        self.peer = 0
        self.state = u''
        self.supported = 0

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'advertised'] = self.advertised
        pyson_object[u'config'] = self.config
        pyson_object[u'curr'] = self.curr
        pyson_object[u'currentSpeed'] = self.current_speed
        pyson_object[u'hardwareAddress'] = self.hardware_address
        pyson_object[u'maxSpeed'] = self.max_speed
        pyson_object[u'name'] = self.name
        pyson_object[u'portId'] = self.port_id
        pyson_object[u'peer'] = self.peer
        pyson_object[u'state'] = self.state
        pyson_object[u'supported'] = self.supported

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'advertised' in pyson_object:
            self.advertised = pyson_object[u'advertised']
        if u'config' in pyson_object:
            self.config = pyson_object[u'config']
        if u'curr' in pyson_object:
            self.curr = pyson_object[u'curr']
        if u'currentSpeed' in pyson_object:
            self.current_speed = pyson_object[u'currentSpeed']
        if u'hardwareAddress' in pyson_object:
            self.hardware_address = pyson_object[u'hardwareAddress']
        if u'maxSpeed' in pyson_object:
            self.max_speed = pyson_object[u'maxSpeed']
        if u'name' in pyson_object:
            self.name = pyson_object[u'name']
        if u'portId' in pyson_object:
            self.port_id = pyson_object[u'portId']
        if u'peer' in pyson_object:
            self.peer = pyson_object[u'peer']
        if u'state' in pyson_object:
            self.state = pyson_object[u'state']
        if u'supported' in pyson_object:
            self.supported = pyson_object[u'supported']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class Group(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Group'
        self.node = u''
        self.buckets = []
        self.group_type = u''
        self.group_id = 0
        self.error_state = u''
        self.errors = []
        self.id = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'node'] = self.node
        # Complex Copy of buckets
        buckets_result = []
        for item_from_buckets in self.buckets:
            buckets_result.append(item_from_buckets.to_pyson())
        pyson_object[u'buckets'] = buckets_result
        pyson_object[u'groupType'] = self.group_type
        pyson_object[u'groupId'] = self.group_id
        pyson_object[u'errorState'] = self.error_state
        pyson_object[u'errors'] = list(self.errors)
        pyson_object[u'id'] = self.id

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'node' in pyson_object:
            self.node = pyson_object[u'node']
        if u'buckets' in pyson_object:
            self.buckets = []
            buckets_json_list = pyson_object[u'buckets']
            for buckets_json_element in buckets_json_list:
                buckets_odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Bucket'
                if u'@odata.type' in buckets_json_element:
                    buckets_odata_type = buckets_json_element[u'@odata.type']
                new_element = Resolver.get_new_object(buckets_odata_type)
                new_element.from_pyson(buckets_json_element)
                self.buckets.append(new_element)
        if u'groupType' in pyson_object:
            self.group_type = pyson_object[u'groupType']
        if u'groupId' in pyson_object:
            self.group_id = pyson_object[u'groupId']
        if u'errorState' in pyson_object:
            self.error_state = pyson_object[u'errorState']
        if u'errors' in pyson_object:
            self.errors = list(pyson_object[u'errors'])
        if u'id' in pyson_object:
            self.id = pyson_object[u'id']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class Bucket(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Bucket'
        self.id = u''
        self.watch_port = 0
        self.watch_group = 0
        self.actions = []

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'id'] = self.id
        pyson_object[u'watchPort'] = self.watch_port
        pyson_object[u'watchGroup'] = self.watch_group
        # Complex Copy of actions
        actions_result = []
        for item_from_actions in self.actions:
            actions_result.append(item_from_actions.to_pyson())
        pyson_object[u'actions'] = actions_result

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'id' in pyson_object:
            self.id = pyson_object[u'id']
        if u'watchPort' in pyson_object:
            self.watch_port = pyson_object[u'watchPort']
        if u'watchGroup' in pyson_object:
            self.watch_group = pyson_object[u'watchGroup']
        if u'actions' in pyson_object:
            self.actions = []
            actions_json_list = pyson_object[u'actions']
            for actions_json_element in actions_json_list:
                actions_odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Action'
                if u'@odata.type' in actions_json_element:
                    actions_odata_type = actions_json_element[u'@odata.type']
                new_element = Resolver.get_new_object(actions_odata_type)
                new_element.from_pyson(actions_json_element)
                self.actions.append(new_element)

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class FlowStat(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.FlowStat'
        self.byte_count = 0
        self.cookie = 0
        self.duration_n_sec = 0
        self.duration_sec = 0
        self.flags = 0
        self.hard_timeout = 0
        self.idle_timeout = 0
        self.packet_count = 0
        self.priority = 0
        self.table_id = 0
        self.match = Match()
        self.instructions = []

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'byteCount'] = self.byte_count
        pyson_object[u'cookie'] = self.cookie
        pyson_object[u'durationNSec'] = self.duration_n_sec
        pyson_object[u'durationSec'] = self.duration_sec
        pyson_object[u'flags'] = self.flags
        pyson_object[u'hardTimeout'] = self.hard_timeout
        pyson_object[u'idleTimeout'] = self.idle_timeout
        pyson_object[u'packetCount'] = self.packet_count
        pyson_object[u'priority'] = self.priority
        pyson_object[u'tableId'] = self.table_id
        pyson_object[u'match'] = self.match.to_pyson()
        # Complex Copy of instructions
        instructions_result = []
        for item_from_instructions in self.instructions:
            instructions_result.append(item_from_instructions.to_pyson())
        pyson_object[u'instructions'] = instructions_result

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'byteCount' in pyson_object:
            self.byte_count = pyson_object[u'byteCount']
        if u'cookie' in pyson_object:
            self.cookie = pyson_object[u'cookie']
        if u'durationNSec' in pyson_object:
            self.duration_n_sec = pyson_object[u'durationNSec']
        if u'durationSec' in pyson_object:
            self.duration_sec = pyson_object[u'durationSec']
        if u'flags' in pyson_object:
            self.flags = pyson_object[u'flags']
        if u'hardTimeout' in pyson_object:
            self.hard_timeout = pyson_object[u'hardTimeout']
        if u'idleTimeout' in pyson_object:
            self.idle_timeout = pyson_object[u'idleTimeout']
        if u'packetCount' in pyson_object:
            self.packet_count = pyson_object[u'packetCount']
        if u'priority' in pyson_object:
            self.priority = pyson_object[u'priority']
        if u'tableId' in pyson_object:
            self.table_id = pyson_object[u'tableId']
        if u'match' in pyson_object:
            match_json_element = pyson_object[u'match']
            match_odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Match'
            if u'@odata.type' in match_json_element:
                    match_odata_type = match_json_element[u'@odata.type']
            self.match = Resolver.get_new_object(match_odata_type)
            self.match.from_pyson(match_json_element)
        if u'instructions' in pyson_object:
            self.instructions = []
            instructions_json_list = pyson_object[u'instructions']
            for instructions_json_element in instructions_json_list:
                instructions_odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Instruction'
                if u'@odata.type' in instructions_json_element:
                    instructions_odata_type = instructions_json_element[u'@odata.type']
                new_element = Resolver.get_new_object(instructions_odata_type)
                new_element.from_pyson(instructions_json_element)
                self.instructions.append(new_element)

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class TableStat(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.TableStat'
        self.table_id = 0
        self.lookup_count = 0
        self.active_count = 0
        self.match_count = 0

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'tableId'] = self.table_id
        pyson_object[u'lookupCount'] = self.lookup_count
        pyson_object[u'activeCount'] = self.active_count
        pyson_object[u'matchCount'] = self.match_count

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'tableId' in pyson_object:
            self.table_id = pyson_object[u'tableId']
        if u'lookupCount' in pyson_object:
            self.lookup_count = pyson_object[u'lookupCount']
        if u'activeCount' in pyson_object:
            self.active_count = pyson_object[u'activeCount']
        if u'matchCount' in pyson_object:
            self.match_count = pyson_object[u'matchCount']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class PortStat(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.PortStat'
        self.collisions = 0
        self.port_no = 0
        self.rx_crc_err = 0
        self.rx_dropped = 0
        self.rx_errors = 0
        self.rx_frame_err = 0
        self.rx_over_error = 0
        self.rx_packets = 0
        self.rx_bytes = 0
        self.tx_bytes = 0
        self.tx_dropped = 0
        self.tx_errors = 0
        self.tx_packets = 0

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'collisions'] = self.collisions
        pyson_object[u'portNo'] = self.port_no
        pyson_object[u'rxCrcErr'] = self.rx_crc_err
        pyson_object[u'rxDropped'] = self.rx_dropped
        pyson_object[u'rxErrors'] = self.rx_errors
        pyson_object[u'rxFrameErr'] = self.rx_frame_err
        pyson_object[u'rxOverError'] = self.rx_over_error
        pyson_object[u'rxPackets'] = self.rx_packets
        pyson_object[u'rxBytes'] = self.rx_bytes
        pyson_object[u'txBytes'] = self.tx_bytes
        pyson_object[u'txDropped'] = self.tx_dropped
        pyson_object[u'txErrors'] = self.tx_errors
        pyson_object[u'txPackets'] = self.tx_packets

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'collisions' in pyson_object:
            self.collisions = pyson_object[u'collisions']
        if u'portNo' in pyson_object:
            self.port_no = pyson_object[u'portNo']
        if u'rxCrcErr' in pyson_object:
            self.rx_crc_err = pyson_object[u'rxCrcErr']
        if u'rxDropped' in pyson_object:
            self.rx_dropped = pyson_object[u'rxDropped']
        if u'rxErrors' in pyson_object:
            self.rx_errors = pyson_object[u'rxErrors']
        if u'rxFrameErr' in pyson_object:
            self.rx_frame_err = pyson_object[u'rxFrameErr']
        if u'rxOverError' in pyson_object:
            self.rx_over_error = pyson_object[u'rxOverError']
        if u'rxPackets' in pyson_object:
            self.rx_packets = pyson_object[u'rxPackets']
        if u'rxBytes' in pyson_object:
            self.rx_bytes = pyson_object[u'rxBytes']
        if u'txBytes' in pyson_object:
            self.tx_bytes = pyson_object[u'txBytes']
        if u'txDropped' in pyson_object:
            self.tx_dropped = pyson_object[u'txDropped']
        if u'txErrors' in pyson_object:
            self.tx_errors = pyson_object[u'txErrors']
        if u'txPackets' in pyson_object:
            self.tx_packets = pyson_object[u'txPackets']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class FlowStats(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.FlowStats'
        self.stats = []
        self.data_path_id = 0
        self.id = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        # Complex Copy of stats
        stats_result = []
        for item_from_stats in self.stats:
            stats_result.append(item_from_stats.to_pyson())
        pyson_object[u'stats'] = stats_result
        pyson_object[u'dataPathId'] = self.data_path_id
        pyson_object[u'id'] = self.id

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'stats' in pyson_object:
            self.stats = []
            stats_json_list = pyson_object[u'stats']
            for stats_json_element in stats_json_list:
                stats_odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.FlowStat'
                if u'@odata.type' in stats_json_element:
                    stats_odata_type = stats_json_element[u'@odata.type']
                new_element = Resolver.get_new_object(stats_odata_type)
                new_element.from_pyson(stats_json_element)
                self.stats.append(new_element)
        if u'dataPathId' in pyson_object:
            self.data_path_id = pyson_object[u'dataPathId']
        if u'id' in pyson_object:
            self.id = pyson_object[u'id']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class GroupDesc(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.GroupDesc'
        self.data_path_id = 0
        self.groups = []
        self.id = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'dataPathId'] = self.data_path_id
        # Complex Copy of groups
        groups_result = []
        for item_from_groups in self.groups:
            groups_result.append(item_from_groups.to_pyson())
        pyson_object[u'groups'] = groups_result
        pyson_object[u'id'] = self.id

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'dataPathId' in pyson_object:
            self.data_path_id = pyson_object[u'dataPathId']
        if u'groups' in pyson_object:
            self.groups = []
            groups_json_list = pyson_object[u'groups']
            for groups_json_element in groups_json_list:
                groups_odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Group'
                if u'@odata.type' in groups_json_element:
                    groups_odata_type = groups_json_element[u'@odata.type']
                new_element = Resolver.get_new_object(groups_odata_type)
                new_element.from_pyson(groups_json_element)
                self.groups.append(new_element)
        if u'id' in pyson_object:
            self.id = pyson_object[u'id']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class PortDesc(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.PortDesc'
        self.data_path_id = 0
        self.ports = []
        self.id = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'dataPathId'] = self.data_path_id
        # Complex Copy of ports
        ports_result = []
        for item_from_ports in self.ports:
            ports_result.append(item_from_ports.to_pyson())
        pyson_object[u'ports'] = ports_result
        pyson_object[u'id'] = self.id

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'dataPathId' in pyson_object:
            self.data_path_id = pyson_object[u'dataPathId']
        if u'ports' in pyson_object:
            self.ports = []
            ports_json_list = pyson_object[u'ports']
            for ports_json_element in ports_json_list:
                ports_odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Port'
                if u'@odata.type' in ports_json_element:
                    ports_odata_type = ports_json_element[u'@odata.type']
                new_element = Resolver.get_new_object(ports_odata_type)
                new_element.from_pyson(ports_json_element)
                self.ports.append(new_element)
        if u'id' in pyson_object:
            self.id = pyson_object[u'id']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class DeviceCapability(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.DeviceCapability'
        self.protocol = u''
        self.version = u''
        self.data_path_id = 0
        self.id = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'protocol'] = self.protocol
        pyson_object[u'version'] = self.version
        pyson_object[u'dataPathId'] = self.data_path_id
        pyson_object[u'id'] = self.id

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'protocol' in pyson_object:
            self.protocol = pyson_object[u'protocol']
        if u'version' in pyson_object:
            self.version = pyson_object[u'version']
        if u'dataPathId' in pyson_object:
            self.data_path_id = pyson_object[u'dataPathId']
        if u'id' in pyson_object:
            self.id = pyson_object[u'id']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class TableStats(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.TableStats'
        self.table_stat_list = []
        self.data_path_id = 0
        self.id = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        # Complex Copy of tableStatList
        table_stat_list_result = []
        for item_from_table_stat_list in self.table_stat_list:
            table_stat_list_result.append(item_from_table_stat_list.to_pyson())
        pyson_object[u'tableStatList'] = table_stat_list_result
        pyson_object[u'dataPathId'] = self.data_path_id
        pyson_object[u'id'] = self.id

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'tableStatList' in pyson_object:
            self.table_stat_list = []
            table_stat_list_json_list = pyson_object[u'tableStatList']
            for table_stat_list_json_element in table_stat_list_json_list:
                table_stat_list_odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.TableStat'
                if u'@odata.type' in table_stat_list_json_element:
                    table_stat_list_odata_type = table_stat_list_json_element[u'@odata.type']
                new_element = Resolver.get_new_object(table_stat_list_odata_type)
                new_element.from_pyson(table_stat_list_json_element)
                self.table_stat_list.append(new_element)
        if u'dataPathId' in pyson_object:
            self.data_path_id = pyson_object[u'dataPathId']
        if u'id' in pyson_object:
            self.id = pyson_object[u'id']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class PortStats(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.PortStats'
        self.port_stat_list = []
        self.data_path_id = 0
        self.id = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        # Complex Copy of portStatList
        port_stat_list_result = []
        for item_from_port_stat_list in self.port_stat_list:
            port_stat_list_result.append(item_from_port_stat_list.to_pyson())
        pyson_object[u'portStatList'] = port_stat_list_result
        pyson_object[u'dataPathId'] = self.data_path_id
        pyson_object[u'id'] = self.id

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'portStatList' in pyson_object:
            self.port_stat_list = []
            port_stat_list_json_list = pyson_object[u'portStatList']
            for port_stat_list_json_element in port_stat_list_json_list:
                port_stat_list_odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.PortStat'
                if u'@odata.type' in port_stat_list_json_element:
                    port_stat_list_odata_type = port_stat_list_json_element[u'@odata.type']
                new_element = Resolver.get_new_object(port_stat_list_odata_type)
                new_element.from_pyson(port_stat_list_json_element)
                self.port_stat_list.append(new_element)
        if u'dataPathId' in pyson_object:
            self.data_path_id = pyson_object[u'dataPathId']
        if u'id' in pyson_object:
            self.id = pyson_object[u'id']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class Behavior(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.Common.DataBroker.Types.EventBus.Behaviors.Behavior'
        self.severity = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'severity'] = self.severity

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'severity' in pyson_object:
            self.severity = pyson_object[u'severity']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class RestTransaction(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.Common.RestBroker.Models.RestTransaction'
        self.id = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'id'] = self.id

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'id' in pyson_object:
            self.id = pyson_object[u'id']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class OperationalNode(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.TopologyManager.Nodes.OperationalNode'
        self.mac = u''
        self.is_connected = False
        self.discoverer_list = []
        self.state = u''
        self.trust_state = u''
        self.id = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'mac'] = self.mac
        pyson_object[u'isConnected'] = self.is_connected
        pyson_object[u'discovererList'] = list(self.discoverer_list)
        pyson_object[u'state'] = self.state
        pyson_object[u'trustState'] = self.trust_state
        pyson_object[u'id'] = self.id

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'mac' in pyson_object:
            self.mac = pyson_object[u'mac']
        if u'isConnected' in pyson_object:
            self.is_connected = pyson_object[u'isConnected']
        if u'discovererList' in pyson_object:
            self.discoverer_list = list(pyson_object[u'discovererList'])
        if u'state' in pyson_object:
            self.state = pyson_object[u'state']
        if u'trustState' in pyson_object:
            self.trust_state = pyson_object[u'trustState']
        if u'id' in pyson_object:
            self.id = pyson_object[u'id']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class EventType(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.Common.DataBroker.Types.EventBus.EventType'
        self.type_key = TypeKey()
        self.duration_setting = u''
        self.severity = u''
        self.id = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'typeKey'] = self.type_key.to_pyson()
        pyson_object[u'durationSetting'] = self.duration_setting
        pyson_object[u'severity'] = self.severity
        pyson_object[u'id'] = self.id

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'typeKey' in pyson_object:
            type_key_json_element = pyson_object[u'typeKey']
            type_key_odata_type = u'#Sel.Sel5056.Common.DataBroker.Types.TypeKey'
            if u'@odata.type' in type_key_json_element:
                    type_key_odata_type = type_key_json_element[u'@odata.type']
            self.type_key = Resolver.get_new_object(type_key_odata_type)
            self.type_key.from_pyson(type_key_json_element)
        if u'durationSetting' in pyson_object:
            self.duration_setting = pyson_object[u'durationSetting']
        if u'severity' in pyson_object:
            self.severity = pyson_object[u'severity']
        if u'id' in pyson_object:
            self.id = pyson_object[u'id']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class EventCategory(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.Common.DataBroker.Types.EventBus.EventCategory'
        self.key = u''
        self.behaviors = []
        self.id = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'key'] = self.key
        # Complex Copy of behaviors
        behaviors_result = []
        for item_from_behaviors in self.behaviors:
            behaviors_result.append(item_from_behaviors.to_pyson())
        pyson_object[u'behaviors'] = behaviors_result
        pyson_object[u'id'] = self.id

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'key' in pyson_object:
            self.key = pyson_object[u'key']
        if u'behaviors' in pyson_object:
            self.behaviors = []
            behaviors_json_list = pyson_object[u'behaviors']
            for behaviors_json_element in behaviors_json_list:
                behaviors_odata_type = u'#Sel.Sel5056.Common.DataBroker.Types.EventBus.Behaviors.Behavior'
                if u'@odata.type' in behaviors_json_element:
                    behaviors_odata_type = behaviors_json_element[u'@odata.type']
                new_element = Resolver.get_new_object(behaviors_odata_type)
                new_element.from_pyson(behaviors_json_element)
                self.behaviors.append(new_element)
        if u'id' in pyson_object:
            self.id = pyson_object[u'id']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class Event(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.Common.DataBroker.Types.EventBus.Event'
        self.state = u''
        self.category = EventCategory()
        self.event_type = EventType()
        self.id = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'state'] = self.state
        pyson_object[u'category'] = self.category.to_pyson()
        pyson_object[u'eventType'] = self.event_type.to_pyson()
        pyson_object[u'id'] = self.id

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'state' in pyson_object:
            self.state = pyson_object[u'state']
        if u'category' in pyson_object:
            category_json_element = pyson_object[u'category']
            category_odata_type = u'#Sel.Sel5056.Common.DataBroker.Types.EventBus.EventCategory'
            if u'@odata.type' in category_json_element:
                    category_odata_type = category_json_element[u'@odata.type']
            self.category = Resolver.get_new_object(category_odata_type)
            self.category.from_pyson(category_json_element)
        if u'eventType' in pyson_object:
            event_type_json_element = pyson_object[u'eventType']
            event_type_odata_type = u'#Sel.Sel5056.Common.DataBroker.Types.EventBus.EventType'
            if u'@odata.type' in event_type_json_element:
                    event_type_odata_type = event_type_json_element[u'@odata.type']
            self.event_type = Resolver.get_new_object(event_type_odata_type)
            self.event_type.from_pyson(event_type_json_element)
        if u'id' in pyson_object:
            self.id = pyson_object[u'id']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class OperationalPort(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.TopologyManager.Ports.OperationalPort'
        self.parent_node = u''
        self.is_connected = False
        self.discoverer_list = []
        self.state = u''
        self.trust_state = u''
        self.id = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'parentNode'] = self.parent_node
        pyson_object[u'isConnected'] = self.is_connected
        pyson_object[u'discovererList'] = list(self.discoverer_list)
        pyson_object[u'state'] = self.state
        pyson_object[u'trustState'] = self.trust_state
        pyson_object[u'id'] = self.id

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'parentNode' in pyson_object:
            self.parent_node = pyson_object[u'parentNode']
        if u'isConnected' in pyson_object:
            self.is_connected = pyson_object[u'isConnected']
        if u'discovererList' in pyson_object:
            self.discoverer_list = list(pyson_object[u'discovererList'])
        if u'state' in pyson_object:
            self.state = pyson_object[u'state']
        if u'trustState' in pyson_object:
            self.trust_state = pyson_object[u'trustState']
        if u'id' in pyson_object:
            self.id = pyson_object[u'id']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class OperationalLink(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.TopologyManager.Links.OperationalLink'
        self.end_points = []
        self.is_connected = False
        self.discoverer_list = []
        self.state = u''
        self.trust_state = u''
        self.id = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'endPoints'] = list(self.end_points)
        pyson_object[u'isConnected'] = self.is_connected
        pyson_object[u'discovererList'] = list(self.discoverer_list)
        pyson_object[u'state'] = self.state
        pyson_object[u'trustState'] = self.trust_state
        pyson_object[u'id'] = self.id

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'endPoints' in pyson_object:
            self.end_points = list(pyson_object[u'endPoints'])
        if u'isConnected' in pyson_object:
            self.is_connected = pyson_object[u'isConnected']
        if u'discovererList' in pyson_object:
            self.discoverer_list = list(pyson_object[u'discovererList'])
        if u'state' in pyson_object:
            self.state = pyson_object[u'state']
        if u'trustState' in pyson_object:
            self.trust_state = pyson_object[u'trustState']
        if u'id' in pyson_object:
            self.id = pyson_object[u'id']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class VlanVid(OxmTlv):
    def __init__(self):
        super(VlanVid, self).__init__()
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.MatchFields.VlanVid'
        self.value = 0

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        super(VlanVid, self)._add_pyson(pyson_object)
        pyson_object[u'value'] = self.value

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        super(VlanVid, self)._parse_pyson(pyson_object)
        if u'value' in pyson_object:
            self.value = pyson_object[u'value']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class GroupAction(Action):
    def __init__(self):
        super(GroupAction, self).__init__()
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.GroupAction'
        self.group_id = 0

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        super(GroupAction, self)._add_pyson(pyson_object)
        pyson_object[u'groupId'] = self.group_id

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        super(GroupAction, self)._parse_pyson(pyson_object)
        if u'groupId' in pyson_object:
            self.group_id = pyson_object[u'groupId']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class PushVlanAction(Action):
    def __init__(self):
        super(PushVlanAction, self).__init__()
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.PushVlanAction'
        self.ether_type = 0

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        super(PushVlanAction, self)._add_pyson(pyson_object)
        pyson_object[u'etherType'] = self.ether_type

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        super(PushVlanAction, self)._parse_pyson(pyson_object)
        if u'etherType' in pyson_object:
            self.ether_type = pyson_object[u'etherType']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class SetFieldAction(Action):
    def __init__(self):
        super(SetFieldAction, self).__init__()
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.SetFieldAction'
        self.field = OxmTlv()

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        super(SetFieldAction, self)._add_pyson(pyson_object)
        pyson_object[u'field'] = self.field.to_pyson()

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        super(SetFieldAction, self)._parse_pyson(pyson_object)
        if u'field' in pyson_object:
            field_json_element = pyson_object[u'field']
            field_odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.MatchFields.OxmTlv'
            if u'@odata.type' in field_json_element:
                    field_odata_type = field_json_element[u'@odata.type']
            self.field = Resolver.get_new_object(field_odata_type)
            self.field.from_pyson(field_json_element)

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class GoToTable(Instruction):
    def __init__(self):
        super(GoToTable, self).__init__()
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.GoToTable'
        self.table_id = 0

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        super(GoToTable, self)._add_pyson(pyson_object)
        pyson_object[u'tableId'] = self.table_id

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        super(GoToTable, self)._parse_pyson(pyson_object)
        if u'tableId' in pyson_object:
            self.table_id = pyson_object[u'tableId']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class AlarmBehavior(Behavior):
    def __init__(self):
        super(AlarmBehavior, self).__init__()
        self._odata_type = u'#Sel.Sel5056.Common.DataBroker.Types.EventBus.Behaviors.AlarmBehavior'

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        super(AlarmBehavior, self)._add_pyson(pyson_object)
        pass

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        super(AlarmBehavior, self)._parse_pyson(pyson_object)
        pass

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class SysLogBehavior(Behavior):
    def __init__(self):
        super(SysLogBehavior, self).__init__()
        self._odata_type = u'#Sel.Sel5056.Common.DataBroker.Types.EventBus.Behaviors.SysLogBehavior'

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        super(SysLogBehavior, self)._add_pyson(pyson_object)
        pass

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        super(SysLogBehavior, self)._parse_pyson(pyson_object)
        pass

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class ControllerNode(OperationalNode):
    def __init__(self):
        super(ControllerNode, self).__init__()
        self._odata_type = u'#Sel.Sel5056.TopologyManager.Nodes.ControllerNode'

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        super(ControllerNode, self)._add_pyson(pyson_object)
        pass

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        super(ControllerNode, self)._parse_pyson(pyson_object)
        pass

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class ClearedEventType(EventType):
    def __init__(self):
        super(ClearedEventType, self).__init__()
        self._odata_type = u'#Sel.Sel5056.Common.DataBroker.Types.EventBus.ClearedEventType'
        self.linked_type_key = TypeKey()

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        super(ClearedEventType, self)._add_pyson(pyson_object)
        pyson_object[u'linkedTypeKey'] = self.linked_type_key.to_pyson()

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        super(ClearedEventType, self)._parse_pyson(pyson_object)
        if u'linkedTypeKey' in pyson_object:
            linked_type_key_json_element = pyson_object[u'linkedTypeKey']
            linked_type_key_odata_type = u'#Sel.Sel5056.Common.DataBroker.Types.TypeKey'
            if u'@odata.type' in linked_type_key_json_element:
                    linked_type_key_odata_type = linked_type_key_json_element[u'@odata.type']
            self.linked_type_key = Resolver.get_new_object(linked_type_key_odata_type)
            self.linked_type_key.from_pyson(linked_type_key_json_element)

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class HostNode(OperationalNode):
    def __init__(self):
        super(HostNode, self).__init__()
        self._odata_type = u'#Sel.Sel5056.TopologyManager.HostNode'
        self.ip_address = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        super(HostNode, self)._add_pyson(pyson_object)
        pyson_object[u'ipAddress'] = self.ip_address

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        super(HostNode, self)._parse_pyson(pyson_object)
        if u'ipAddress' in pyson_object:
            self.ip_address = pyson_object[u'ipAddress']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class VlanPcp(OxmTlv):
    def __init__(self):
        super(VlanPcp, self).__init__()
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.MatchFields.VlanPcp'
        self.value = 0

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        super(VlanPcp, self)._add_pyson(pyson_object)
        pyson_object[u'value'] = self.value

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        super(VlanPcp, self)._parse_pyson(pyson_object)
        if u'value' in pyson_object:
            self.value = pyson_object[u'value']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class PopVlanAction(Action):
    def __init__(self):
        super(PopVlanAction, self).__init__()
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.PopVlanAction'

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        super(PopVlanAction, self)._add_pyson(pyson_object)
        pass

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        super(PopVlanAction, self)._parse_pyson(pyson_object)
        pass

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class WriteActions(Instruction):
    def __init__(self):
        super(WriteActions, self).__init__()
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.WriteActions'

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        super(WriteActions, self)._add_pyson(pyson_object)
        pass

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        super(WriteActions, self)._parse_pyson(pyson_object)
        pass

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class WebDataBehavior(Behavior):
    def __init__(self):
        super(WebDataBehavior, self).__init__()
        self._odata_type = u'#Sel.Sel5056.Common.DataBroker.Types.EventBus.Behaviors.WebDataBehavior'

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        super(WebDataBehavior, self)._add_pyson(pyson_object)
        pass

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        super(WebDataBehavior, self)._parse_pyson(pyson_object)
        pass

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class EthernetPort(OperationalPort):
    def __init__(self):
        super(EthernetPort, self).__init__()
        self._odata_type = u'#Sel.Sel5056.TopologyManager.Ports.EthernetPort'
        self.mac_address = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        super(EthernetPort, self)._add_pyson(pyson_object)
        pyson_object[u'macAddress'] = self.mac_address

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        super(EthernetPort, self)._parse_pyson(pyson_object)
        if u'macAddress' in pyson_object:
            self.mac_address = pyson_object[u'macAddress']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class HostInterfacePort(EthernetPort):
    def __init__(self):
        super(HostInterfacePort, self).__init__()
        self._odata_type = u'#Sel.Sel5056.TopologyManager.HostInterfacePort'

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        super(HostInterfacePort, self)._add_pyson(pyson_object)
        pass

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        super(HostInterfacePort, self)._parse_pyson(pyson_object)
        pass

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class OutputAction(Action):
    def __init__(self):
        super(OutputAction, self).__init__()
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.OutputAction'
        self.out_port = 0
        self.max_length = 0

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        super(OutputAction, self)._add_pyson(pyson_object)
        pyson_object[u'outPort'] = self.out_port
        pyson_object[u'maxLength'] = self.max_length

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        super(OutputAction, self)._parse_pyson(pyson_object)
        if u'outPort' in pyson_object:
            self.out_port = pyson_object[u'outPort']
        if u'maxLength' in pyson_object:
            self.max_length = pyson_object[u'maxLength']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class LocalLogBehavior(Behavior):
    def __init__(self):
        super(LocalLogBehavior, self).__init__()
        self._odata_type = u'#Sel.Sel5056.Common.DataBroker.Types.EventBus.Behaviors.LocalLogBehavior'

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        super(LocalLogBehavior, self)._add_pyson(pyson_object)
        pass

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        super(LocalLogBehavior, self)._parse_pyson(pyson_object)
        pass

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class OpenFlowPort(EthernetPort):
    def __init__(self):
        super(OpenFlowPort, self).__init__()
        self._odata_type = u'#Sel.Sel5056.TopologyManager.Ports.OpenFlowPort'
        self.data_path_id = 0
        self.advertised = 0
        self.config = 0
        self.current_features = 0
        self.current_speed = 0
        self.hardware_address = u''
        self.max_speed = 0
        self.name = u''
        self.port_id = 0
        self.peer = 0
        self.of_state = u''
        self.supported = 0

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        super(OpenFlowPort, self)._add_pyson(pyson_object)
        pyson_object[u'dataPathId'] = self.data_path_id
        pyson_object[u'advertised'] = self.advertised
        pyson_object[u'config'] = self.config
        pyson_object[u'currentFeatures'] = self.current_features
        pyson_object[u'currentSpeed'] = self.current_speed
        pyson_object[u'hardwareAddress'] = self.hardware_address
        pyson_object[u'maxSpeed'] = self.max_speed
        pyson_object[u'name'] = self.name
        pyson_object[u'portId'] = self.port_id
        pyson_object[u'peer'] = self.peer
        pyson_object[u'ofState'] = self.of_state
        pyson_object[u'supported'] = self.supported

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        super(OpenFlowPort, self)._parse_pyson(pyson_object)
        if u'dataPathId' in pyson_object:
            self.data_path_id = pyson_object[u'dataPathId']
        if u'advertised' in pyson_object:
            self.advertised = pyson_object[u'advertised']
        if u'config' in pyson_object:
            self.config = pyson_object[u'config']
        if u'currentFeatures' in pyson_object:
            self.current_features = pyson_object[u'currentFeatures']
        if u'currentSpeed' in pyson_object:
            self.current_speed = pyson_object[u'currentSpeed']
        if u'hardwareAddress' in pyson_object:
            self.hardware_address = pyson_object[u'hardwareAddress']
        if u'maxSpeed' in pyson_object:
            self.max_speed = pyson_object[u'maxSpeed']
        if u'name' in pyson_object:
            self.name = pyson_object[u'name']
        if u'portId' in pyson_object:
            self.port_id = pyson_object[u'portId']
        if u'peer' in pyson_object:
            self.peer = pyson_object[u'peer']
        if u'ofState' in pyson_object:
            self.of_state = pyson_object[u'ofState']
        if u'supported' in pyson_object:
            self.supported = pyson_object[u'supported']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class ApplyActions(Instruction):
    def __init__(self):
        super(ApplyActions, self).__init__()
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.ApplyActions'

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        super(ApplyActions, self)._add_pyson(pyson_object)
        pass

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        super(ApplyActions, self)._parse_pyson(pyson_object)
        pass

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class OpenFlowNode(OperationalNode):
    def __init__(self):
        super(OpenFlowNode, self).__init__()
        self._odata_type = u'#Sel.Sel5056.TopologyManager.Nodes.OpenFlowNode'
        self.ip_address = u''
        self.name = u''
        self.data_path_id = 0

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        super(OpenFlowNode, self)._add_pyson(pyson_object)
        pyson_object[u'ipAddress'] = self.ip_address
        pyson_object[u'name'] = self.name
        pyson_object[u'dataPathId'] = self.data_path_id

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        super(OpenFlowNode, self)._parse_pyson(pyson_object)
        if u'ipAddress' in pyson_object:
            self.ip_address = pyson_object[u'ipAddress']
        if u'name' in pyson_object:
            self.name = pyson_object[u'name']
        if u'dataPathId' in pyson_object:
            self.data_path_id = pyson_object[u'dataPathId']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


#
# Begin IOC Container Definition (Dependency Resolvers)
#


class Resolver(object):
    def get_new_object(self, odata_type):
        return Resolver.get_new_object(odata_type)

    @staticmethod
    def get_new_object(odata_type):
        result = None
        if odata_type == u"#Sel.Sel5056.TopologyManager.Ports.OpenFlowPort":
            result = OpenFlowPort()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.MatchFields.VlanVid":
            result = VlanVid()
        elif odata_type == u"#Sel.Sel5056.TopologyManager.Ports.OperationalPort":
            result = OperationalPort()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.SetFieldAction":
            result = SetFieldAction()
        elif odata_type == u"#Sel.Sel5056.TopologyManager.Nodes.OperationalNode":
            result = OperationalNode()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.GoToTable":
            result = GoToTable()
        elif odata_type == u"#Sel.Sel5056.Common.DataBroker.Types.EventBus.EventType":
            result = EventType()
        elif odata_type == u"#Sel.Sel5056.TopologyManager.HostNode":
            result = HostNode()
        elif odata_type == u"#Sel.Sel5056.TopologyManager.Nodes.ControllerNode":
            result = ControllerNode()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Instruction":
            result = Instruction()
        elif odata_type == u"#Sel.Sel5056.Common.DataBroker.Types.EventBus.Behaviors.SysLogBehavior":
            result = SysLogBehavior()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.OutputAction":
            result = OutputAction()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Bucket":
            result = Bucket()
        elif odata_type == u"#Sel.Sel5056.TopologyManager.HostInterfacePort":
            result = HostInterfacePort()
        elif odata_type == u"#Sel.Sel5056.Common.DataBroker.Types.EventBus.Event":
            result = Event()
        elif odata_type == u"#Sel.Sel5056.Common.DataBroker.Types.EventBus.EventCategory":
            result = EventCategory()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.PortStats":
            result = PortStats()
        elif odata_type == u"#Sel.Sel5056.Common.DataBroker.Types.EventBus.Behaviors.LocalLogBehavior":
            result = LocalLogBehavior()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Group":
            result = Group()
        elif odata_type == u"#Sel.Sel5056.Common.RestBroker.Models.RestTransaction":
            result = RestTransaction()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.PortDesc":
            result = PortDesc()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Match":
            result = Match()
        elif odata_type == u"#Sel.Sel5056.TopologyManager.Ports.EthernetPort":
            result = EthernetPort()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.TableStats":
            result = TableStats()
        elif odata_type == u"#Sel.Sel5056.Common.DataBroker.Types.EventBus.ClearedEventType":
            result = ClearedEventType()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.TableStat":
            result = TableStat()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.WriteActions":
            result = WriteActions()
        elif odata_type == u"#Sel.Sel5056.Common.DataBroker.Types.EventBus.Behaviors.WebDataBehavior":
            result = WebDataBehavior()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.FlowStats":
            result = FlowStats()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.ApplyActions":
            result = ApplyActions()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.PortStat":
            result = PortStat()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.FlowStat":
            result = FlowStat()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.GroupDesc":
            result = GroupDesc()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.MatchFields.OxmTlv":
            result = OxmTlv()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Port":
            result = Port()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.DeviceCapability":
            result = DeviceCapability()
        elif odata_type == u"#Sel.Sel5056.TopologyManager.Links.OperationalLink":
            result = OperationalLink()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.GroupAction":
            result = GroupAction()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.PushVlanAction":
            result = PushVlanAction()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Action":
            result = Action()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.PopVlanAction":
            result = PopVlanAction()
        elif odata_type == u"#Sel.Sel5056.Common.DataBroker.Types.TypeKey":
            result = TypeKey()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.MatchFields.VlanPcp":
            result = VlanPcp()
        elif odata_type == u"#Sel.Sel5056.Common.DataBroker.Types.EventBus.Behaviors.AlarmBehavior":
            result = AlarmBehavior()
        elif odata_type == u"#Sel.Sel5056.TopologyManager.Nodes.OpenFlowNode":
            result = OpenFlowNode()
        elif odata_type == u"#Sel.Sel5056.Common.DataBroker.Types.EventBus.Behaviors.Behavior":
            result = Behavior()
        return result
