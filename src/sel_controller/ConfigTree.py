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
    def failure():
        return u"Failure"

    @staticmethod
    def success():
        return u"Success"

    @staticmethod
    def in_progress():
        return u"InProgress"


class CertificatePurpose(object):

    @staticmethod
    def web_server():
        return u"WebServer"

    @staticmethod
    def internal_certificate_authority():
        return u"InternalCertificateAuthority"


class DurationType(object):

    @staticmethod
    def momentary():
        return u"Momentary"

    @staticmethod
    def persistent():
        return u"Persistent"


class SeverityLevel(object):

    @staticmethod
    def emergency():
        return u"Emergency"

    @staticmethod
    def warning():
        return u"Warning"

    @staticmethod
    def debug():
        return u"Debug"

    @staticmethod
    def critical():
        return u"Critical"

    @staticmethod
    def notice():
        return u"Notice"

    @staticmethod
    def error():
        return u"Error"

    @staticmethod
    def alert():
        return u"Alert"

    @staticmethod
    def informational():
        return u"Informational"


class DiscoveryTrustState(object):

    @staticmethod
    def user():
        return u"User"

    @staticmethod
    def internal():
        return u"Internal"

    @staticmethod
    def certificate():
        return u"Certificate"

    @staticmethod
    def untrusted():
        return u"Untrusted"


class State(object):

    @staticmethod
    def none():
        return u"None"

    @staticmethod
    def configured():
        return u"Configured"

    @staticmethod
    def disconnected():
        return u"Disconnected"

    @staticmethod
    def unadopted():
        return u"Unadopted"

    @staticmethod
    def established():
        return u"Established"

    @staticmethod
    def adopted():
        return u"Adopted"


# Container
# --ConfigTree


class ModuleSettingsEntityAccess(EntityAccess):
    def __init__(self, session):
        super(ModuleSettingsEntityAccess, self).__init__(session, u'default/config/', Resolver())
        self.entity_base_name = u"moduleSettings"
        self.entity_odata_type = u"#Sel.Sel5056.Common.DataBroker.Types.ModuleSettings"


class NodesEntityAccess(EntityAccess):
    def __init__(self, session):
        super(NodesEntityAccess, self).__init__(session, u'default/config/', Resolver())
        self.entity_base_name = u"nodes"
        self.entity_odata_type = u"#Sel.Sel5056.TopologyManager.Nodes.ConfigNode"


class PortsEntityAccess(EntityAccess):
    def __init__(self, session):
        super(PortsEntityAccess, self).__init__(session, u'default/config/', Resolver())
        self.entity_base_name = u"ports"
        self.entity_odata_type = u"#Sel.Sel5056.TopologyManager.Ports.ConfigPort"


class LinksEntityAccess(EntityAccess):
    def __init__(self, session):
        super(LinksEntityAccess, self).__init__(session, u'default/config/', Resolver())
        self.entity_base_name = u"links"
        self.entity_odata_type = u"#Sel.Sel5056.TopologyManager.Links.ConfigLink"


class ExternalCertificateInfoEntityAccess(EntityAccess):
    def __init__(self, session):
        super(ExternalCertificateInfoEntityAccess, self).__init__(session, u'default/config/', Resolver())
        self.entity_base_name = u"externalCertificateInfo"
        self.entity_odata_type = u"#Sel.Sel5056.Common.TrustAuthority.DataTreeObjects.ExternalCertificateInfo"


class EventTypesEntityAccess(EntityAccess):
    def __init__(self, session):
        super(EventTypesEntityAccess, self).__init__(session, u'default/config/', Resolver())
        self.entity_base_name = u"eventTypes"
        self.entity_odata_type = u"#Sel.Sel5056.Common.DataBroker.Types.EventBus.EventType"


class EventCategoriesEntityAccess(EntityAccess):
    def __init__(self, session):
        super(EventCategoriesEntityAccess, self).__init__(session, u'default/config/', Resolver())
        self.entity_base_name = u"eventCategories"
        self.entity_odata_type = u"#Sel.Sel5056.Common.DataBroker.Types.EventBus.EventCategory"


class FlowsEntityAccess(EntityAccess):
    def __init__(self, session):
        super(FlowsEntityAccess, self).__init__(session, u'default/config/', Resolver())
        self.entity_base_name = u"flows"
        self.entity_odata_type = u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Flow"


class GroupsEntityAccess(EntityAccess):
    def __init__(self, session):
        super(GroupsEntityAccess, self).__init__(session, u'default/config/', Resolver())
        self.entity_base_name = u"groups"
        self.entity_odata_type = u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Group"


class FlowSetEntityAccess(EntityAccess):
    def __init__(self, session):
        super(FlowSetEntityAccess, self).__init__(session, u'default/config/', Resolver())
        self.entity_base_name = u"flowSet"
        self.entity_odata_type = u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.FlowSet"


class PreferencesEntityAccess(EntityAccess):
    def __init__(self, session):
        super(PreferencesEntityAccess, self).__init__(session, u'default/config/', Resolver())
        self.entity_base_name = u"preferences"
        self.entity_odata_type = u"#Sel.Sel5056.UserPreferences.Preference"


class TransactionsEntityAccess(EntityAccess):
    def __init__(self, session):
        super(TransactionsEntityAccess, self).__init__(session, u'default/config/', Resolver())
        self.entity_base_name = u"transactions"
        self.entity_odata_type = u"#Sel.Sel5056.Common.RestBroker.Models.RestTransaction"

    def commit(self, item):
        pyson_payload = {}
        item_id = item.id
        return self.execute_action(item_id, pyson_payload, u'Sel', u'Commit')


class OfpActionType(object):

    @staticmethod
    def set_field():
        return u"SetField"

    @staticmethod
    def set_nw_ttl():
        return u"SetNwTtl"

    @staticmethod
    def pop_vlan():
        return u"PopVlan"

    @staticmethod
    def group():
        return u"Group"

    @staticmethod
    def pop_pbb():
        return u"PopPbb"

    @staticmethod
    def output():
        return u"Output"

    @staticmethod
    def dec_mpls_ttl():
        return u"DecMplsTtl"

    @staticmethod
    def experimenter():
        return u"Experimenter"

    @staticmethod
    def copy_ttl_out():
        return u"CopyTtlOut"

    @staticmethod
    def push_mpls():
        return u"PushMpls"

    @staticmethod
    def push_pbb():
        return u"PushPbb"

    @staticmethod
    def dec_nw_ttl():
        return u"DecNwTtl"

    @staticmethod
    def set_queue():
        return u"SetQueue"

    @staticmethod
    def pop_mpls():
        return u"PopMpls"

    @staticmethod
    def set_mpls_ttl():
        return u"SetMplsTtl"

    @staticmethod
    def push_vlan():
        return u"PushVlan"

    @staticmethod
    def copy_ttl_in():
        return u"CopyTtlIn"


class OfpInstructionType(object):

    @staticmethod
    def clear_actions():
        return u"ClearActions"

    @staticmethod
    def write_metadata():
        return u"WriteMetadata"

    @staticmethod
    def apply_actions():
        return u"ApplyActions"

    @staticmethod
    def experimenter():
        return u"Experimenter"

    @staticmethod
    def goto_table():
        return u"GotoTable"

    @staticmethod
    def write_actions():
        return u"WriteActions"

    @staticmethod
    def meter():
        return u"Meter"


class OfpGroupType(object):

    @staticmethod
    def fast_failover():
        return u"FastFailover"

    @staticmethod
    def all():
        return u"All"

    @staticmethod
    def indirect():
        return u"Indirect"

    @staticmethod
    def select():
        return u"Select"


class ConfigPort(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.TopologyManager.Ports.ConfigPort'
        self.display_name = u''
        self.state = u''
        self.id = u''
        self.linked_key = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'displayName'] = self.display_name
        pyson_object[u'state'] = self.state
        pyson_object[u'id'] = self.id
        pyson_object[u'linkedKey'] = self.linked_key

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'displayName' in pyson_object:
            self.display_name = pyson_object[u'displayName']
        if u'state' in pyson_object:
            self.state = pyson_object[u'state']
        if u'id' in pyson_object:
            self.id = pyson_object[u'id']
        if u'linkedKey' in pyson_object:
            self.linked_key = pyson_object[u'linkedKey']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


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
        #self.in_port = u''
        #self.eth_dst = u''
        #self.eth_src = u''
        #self.ipv4_dst = u''
        #self.ipv4_src = u''
        #self.eth_type = u''
        #self.tcp_src = u''
        #self.tcp_dst = u''
        #self.udp_src = u''
        #self.udp_dst = u''
        #self.vlan_vid = u''
        #self.vlan_pcp = u''
        #self.ip_proto = u''
        self.in_port = None
        self.eth_dst = None
        self.eth_src = None
        self.ipv4_dst = None
        self.ipv4_src = None
        self.eth_type = None
        self.tcp_src = None
        self.tcp_dst = None
        self.udp_src = None
        self.udp_dst = None
        self.vlan_vid = None
        self.vlan_pcp = None
        self.ip_proto = None

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


class Flow(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Flow'
        self.node = u''
        self.cookie = 0
        self.table_id = 0
        self.buffer_id = 0
        self.out_group = 0
        self.out_port = 0
        self.priority = 0
        self.match = Match()
        self.instructions = []
        self.enabled = False
        self.error_state = u''
        self.errors = []
        self.id = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'node'] = self.node
        pyson_object[u'cookie'] = self.cookie
        pyson_object[u'tableId'] = self.table_id
        pyson_object[u'bufferId'] = self.buffer_id
        pyson_object[u'outGroup'] = self.out_group
        pyson_object[u'outPort'] = self.out_port
        pyson_object[u'priority'] = self.priority
        pyson_object[u'match'] = self.match.to_pyson()
        # Complex Copy of instructions
        instructions_result = []
        for item_from_instructions in self.instructions:
            instructions_result.append(item_from_instructions.to_pyson())
        pyson_object[u'instructions'] = instructions_result
        pyson_object[u'enabled'] = self.enabled
        pyson_object[u'errorState'] = self.error_state
        pyson_object[u'errors'] = list(self.errors)
        pyson_object[u'id'] = self.id

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'node' in pyson_object:
            self.node = pyson_object[u'node']
        if u'cookie' in pyson_object:
            self.cookie = pyson_object[u'cookie']
        if u'tableId' in pyson_object:
            self.table_id = pyson_object[u'tableId']
        if u'bufferId' in pyson_object:
            self.buffer_id = pyson_object[u'bufferId']
        if u'outGroup' in pyson_object:
            self.out_group = pyson_object[u'outGroup']
        if u'outPort' in pyson_object:
            self.out_port = pyson_object[u'outPort']
        if u'priority' in pyson_object:
            self.priority = pyson_object[u'priority']
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
        if u'enabled' in pyson_object:
            self.enabled = pyson_object[u'enabled']
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


class FlowSet(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.FlowSet'
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


class ModuleSettings(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.Common.DataBroker.Types.ModuleSettings'
        self.module_name = u''
        self.id = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'moduleName'] = self.module_name
        pyson_object[u'id'] = self.id

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'moduleName' in pyson_object:
            self.module_name = pyson_object[u'moduleName']
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


class Setting(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.UserPreferences.Setting'
        self.key = u''
        self.value = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'key'] = self.key
        pyson_object[u'value'] = self.value

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'key' in pyson_object:
            self.key = pyson_object[u'key']
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


class Preference(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.UserPreferences.Preference'
        self.registry = []
        self.id = u''
        self.username = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        # Complex Copy of registry
        registry_result = []
        for item_from_registry in self.registry:
            registry_result.append(item_from_registry.to_pyson())
        pyson_object[u'registry'] = registry_result
        pyson_object[u'id'] = self.id
        pyson_object[u'username'] = self.username

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'registry' in pyson_object:
            self.registry = []
            registry_json_list = pyson_object[u'registry']
            for registry_json_element in registry_json_list:
                registry_odata_type = u'#Sel.Sel5056.UserPreferences.Setting'
                if u'@odata.type' in registry_json_element:
                    registry_odata_type = registry_json_element[u'@odata.type']
                new_element = Resolver.get_new_object(registry_odata_type)
                new_element.from_pyson(registry_json_element)
                self.registry.append(new_element)
        if u'id' in pyson_object:
            self.id = pyson_object[u'id']
        if u'username' in pyson_object:
            self.username = pyson_object[u'username']

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


class ConfigNode(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.TopologyManager.Nodes.ConfigNode'
        self.display_name = u''
        self.state = u''
        self.id = u''
        self.linked_key = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'displayName'] = self.display_name
        pyson_object[u'state'] = self.state
        pyson_object[u'id'] = self.id
        pyson_object[u'linkedKey'] = self.linked_key

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'displayName' in pyson_object:
            self.display_name = pyson_object[u'displayName']
        if u'state' in pyson_object:
            self.state = pyson_object[u'state']
        if u'id' in pyson_object:
            self.id = pyson_object[u'id']
        if u'linkedKey' in pyson_object:
            self.linked_key = pyson_object[u'linkedKey']

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


class ConfigLink(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.TopologyManager.Links.ConfigLink'
        self.display_name = u''
        self.trust_state = u''
        self.state = u''
        self.id = u''
        self.linked_key = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'displayName'] = self.display_name
        pyson_object[u'trustState'] = self.trust_state
        pyson_object[u'state'] = self.state
        pyson_object[u'id'] = self.id
        pyson_object[u'linkedKey'] = self.linked_key

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'displayName' in pyson_object:
            self.display_name = pyson_object[u'displayName']
        if u'trustState' in pyson_object:
            self.trust_state = pyson_object[u'trustState']
        if u'state' in pyson_object:
            self.state = pyson_object[u'state']
        if u'id' in pyson_object:
            self.id = pyson_object[u'id']
        if u'linkedKey' in pyson_object:
            self.linked_key = pyson_object[u'linkedKey']

    def from_json(self, json_string):
        pyson_object = json.loads(json_string)
        self.from_pyson(pyson_object)
        return self

    def to_json(self):
        pyson_object = self.to_pyson()
        json_string = json.dumps(pyson_object, sort_keys=True, indent=4, separators=(u',', u': '))
        return json_string


class ExternalCertificateInfo(object):
    def __init__(self):
        self._odata_type = u'#Sel.Sel5056.Common.TrustAuthority.DataTreeObjects.ExternalCertificateInfo'
        self.name = u''
        self.base64_certificate = u''
        self.thumb_print = u''
        self.certificate_password = u''
        self.purpose = u''
        self.id = u''

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        pyson_object[u'name'] = self.name
        pyson_object[u'base64Certificate'] = self.base64_certificate
        pyson_object[u'thumbPrint'] = self.thumb_print
        pyson_object[u'certificatePassword'] = self.certificate_password
        pyson_object[u'purpose'] = self.purpose
        pyson_object[u'id'] = self.id

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        if u'name' in pyson_object:
            self.name = pyson_object[u'name']
        if u'base64Certificate' in pyson_object:
            self.base64_certificate = pyson_object[u'base64Certificate']
        if u'thumbPrint' in pyson_object:
            self.thumb_print = pyson_object[u'thumbPrint']
        if u'certificatePassword' in pyson_object:
            self.certificate_password = pyson_object[u'certificatePassword']
        if u'purpose' in pyson_object:
            self.purpose = pyson_object[u'purpose']
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


class SecurityManagerSettings(ModuleSettings):
    def __init__(self):
        super(SecurityManagerSettings, self).__init__()
        self._odata_type = u'#Sel.Sel5056.Common.SecurityManager.SecurityManagerSettings'
        self.maximum_login_attempts = 0
        self.lockout_seconds = 0

    def to_pyson(self):
        pyson_object = {u'@odata.type': self._odata_type}
        self._add_pyson(pyson_object)
        return pyson_object

    def _add_pyson(self, pyson_object):
        super(SecurityManagerSettings, self)._add_pyson(pyson_object)
        pyson_object[u'maximumLoginAttempts'] = self.maximum_login_attempts
        pyson_object[u'lockoutSeconds'] = self.lockout_seconds

    def from_pyson(self, pyson_object):
        self._parse_pyson(pyson_object)
        return pyson_object

    def _parse_pyson(self, pyson_object):
        super(SecurityManagerSettings, self)._parse_pyson(pyson_object)
        if u'maximumLoginAttempts' in pyson_object:
            self.maximum_login_attempts = pyson_object[u'maximumLoginAttempts']
        if u'lockoutSeconds' in pyson_object:
            self.lockout_seconds = pyson_object[u'lockoutSeconds']

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
        if odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Bucket":
            result = Bucket()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.OutputAction":
            result = OutputAction()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.GroupAction":
            result = GroupAction()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.MatchFields.VlanPcp":
            result = VlanPcp()
        elif odata_type == u"#Sel.Sel5056.UserPreferences.Preference":
            result = Preference()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Flow":
            result = Flow()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.MatchFields.OxmTlv":
            result = OxmTlv()
        elif odata_type == u"#Sel.Sel5056.TopologyManager.Links.ConfigLink":
            result = ConfigLink()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Match":
            result = Match()
        elif odata_type == u"#Sel.Sel5056.Common.DataBroker.Types.EventBus.Behaviors.WebDataBehavior":
            result = WebDataBehavior()
        elif odata_type == u"#Sel.Sel5056.TopologyManager.Nodes.ConfigNode":
            result = ConfigNode()
        elif odata_type == u"#Sel.Sel5056.Common.DataBroker.Types.ModuleSettings":
            result = ModuleSettings()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.WriteActions":
            result = WriteActions()
        elif odata_type == u"#Sel.Sel5056.Common.TrustAuthority.DataTreeObjects.ExternalCertificateInfo":
            result = ExternalCertificateInfo()
        elif odata_type == u"#Sel.Sel5056.Common.SecurityManager.SecurityManagerSettings":
            result = SecurityManagerSettings()
        elif odata_type == u"#Sel.Sel5056.Common.DataBroker.Types.EventBus.EventType":
            result = EventType()
        elif odata_type == u"#Sel.Sel5056.Common.DataBroker.Types.TypeKey":
            result = TypeKey()
        elif odata_type == u"#Sel.Sel5056.UserPreferences.Setting":
            result = Setting()
        elif odata_type == u"#Sel.Sel5056.Common.DataBroker.Types.EventBus.ClearedEventType":
            result = ClearedEventType()
        elif odata_type == u"#Sel.Sel5056.Common.DataBroker.Types.EventBus.Behaviors.LocalLogBehavior":
            result = LocalLogBehavior()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.FlowSet":
            result = FlowSet()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Action":
            result = Action()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.PushVlanAction":
            result = PushVlanAction()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Group":
            result = Group()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.PopVlanAction":
            result = PopVlanAction()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.MatchFields.VlanVid":
            result = VlanVid()
        elif odata_type == u"#Sel.Sel5056.Common.DataBroker.Types.EventBus.Behaviors.Behavior":
            result = Behavior()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.Instruction":
            result = Instruction()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.SetFieldAction":
            result = SetFieldAction()
        elif odata_type == u"#Sel.Sel5056.Common.RestBroker.Models.RestTransaction":
            result = RestTransaction()
        elif odata_type == u"#Sel.Sel5056.Common.DataBroker.Types.EventBus.Behaviors.SysLogBehavior":
            result = SysLogBehavior()
        elif odata_type == u"#Sel.Sel5056.Common.DataBroker.Types.EventBus.EventCategory":
            result = EventCategory()
        elif odata_type == u"#Sel.Sel5056.Common.DataBroker.Types.EventBus.Behaviors.AlarmBehavior":
            result = AlarmBehavior()
        elif odata_type == u"#Sel.Sel5056.TopologyManager.Ports.ConfigPort":
            result = ConfigPort()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.GoToTable":
            result = GoToTable()
        elif odata_type == u"#Sel.Sel5056.OpenFlowPlugin.DataTreeObjects.ApplyActions":
            result = ApplyActions()
        return result
