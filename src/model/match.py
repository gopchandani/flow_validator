__author__ = 'Rakesh Kumar'

import sys
from netaddr import IPNetwork
from UserDict import DictMixin
from sel_controller import ConfigTree

field_names = ["in_port",
               "ethernet_type",
               "ethernet_source",
               "ethernet_destination",
               "src_ip_addr",
               "dst_ip_addr",
               "ip_protocol",
               "tcp_destination_port",
               "tcp_source_port",
               "udp_destination_port",
               "udp_source_port",
               "vlan_id",
               "has_vlan_tag"]

ryu_field_names_mapping = {"in_port": "in_port",
                           "eth_type": "ethernet_type",
                           "eth_src": "ethernet_source",
                           "eth_dst": "ethernet_destination",
                           "nw_src": "src_ip_addr",
                           "nw_dst": "dst_ip_addr",
                           "ip_proto": "ip_protocol",
                           "tcp_dst": "tcp_destination_port",
                           "tcp_src": "tcp_source_port",
                           "udp_dst": "udp_destination_port",
                           "udp_src": "udp_source_port",
                           "vlan_vid": "vlan_id",
                           "has_vlan_tag": "has_vlan_tag"}

ryu_field_names_mapping_reverse = {"in_port": "in_port",
                                   "ethernet_type": "eth_type",
                                   "ethernet_source": "eth_src",
                                   "ethernet_destination": "eth_dst",
                                   "src_ip_addr": "nw_src",
                                   "dst_ip_addr": "nw_dst",
                                   "ip_protocol": "nw_proto",
                                   "tcp_destination_port": "tcp_dst",
                                   "tcp_source_port": "tcp_src",
                                   "udp_destination_port": "udp_dst",
                                   "udp_source_port": "udp_src",
                                   "vlan_id": "vlan_vid",
                                   "has_vlan_tag": "has_vlan_tag"}

onos_field_names_mapping = {"IN_PORT": "in_port",
                            "ETH_TYPE": "ethernet_type",
                            "ETH_SRC": "ethernet_source",
                            "ETH_DST": "ethernet_destination",
                            "IPV4_SRC": "src_ip_addr",
                            "IPV4_DST": "dst_ip_addr",
                            "IP_PROTO": "ip_protocol",
                            "TCP_DST": "tcp_destination_port",
                            "TCP_SRC": "tcp_source_port",
                            "UDP_DST": "udp_destination_port",
                            "UDP_SRC": "udp_source_port",
                            "VLAN_VID": "vlan_id"}

onos_field_names_mapping_reverse = {"in_port": ("IN_PORT", "port"),
                                    "ethernet_type": ("ETH_TYPE", "ethType"),
                                    "ethernet_source": ("ETH_SRC", "mac"),
                                    "ethernet_destination": ("ETH_DST", "mac"),
                                    "src_ip_addr": ("IPV4_SRC", "ip"),
                                    "dst_ip_addr": ("IPV4_DST", "ip"),
                                    "ip_protocol": ("IP_PROTO", "protocol"),
                                    "tcp_destination_port": ("TCP_DST", "tcpPort"),
                                    "tcp_source_port": ("TCP_SRC", "tcpPort"),
                                    "udp_destination_port": ("UDP_DST", "udpPort"),
                                    "udp_source_port": ("UDP_SRC", "udpPort"),
                                    "vlan_id": ("VLAN_VID", "vlanId")}


class OdlMatchJsonParser():
    def __init__(self, match_raw=None):
        self.field_values = {}
        self._parse(match_raw)

    def _parse(self, match_raw):

        for field_name in field_names:

            try:
                if field_name == "in_port":
                    self[field_name] = match_raw["in-port"]

                elif field_name == "ethernet_type":
                    self[field_name] = match_raw["ethernet-match"]["ethernet-type"]["type"]

                elif field_name == "ethernet_source":
                    self[field_name] = match_raw["ethernet-match"]["ethernet-source"]["address"]

                elif field_name == "ethernet_destination":
                    self[field_name] = match_raw["ethernet-match"]["ethernet-destination"]["address"]

                elif field_name == "src_ip_addr":
                    self[field_name] = match_raw["src_ip_addr"]

                elif field_name == "dst_ip_addr":
                    self[field_name] = match_raw["dst_ip_addr"]

                elif field_name == "ip_protocol":
                    self[field_name] = match_raw["ip-match"]["ip-protocol"]

                elif field_name == "tcp_destination_port":
                    self[field_name] = match_raw["tcp-destination-port"]

                elif field_name == "tcp_source_port":
                    self[field_name] = match_raw["tcp-source-port"]

                elif field_name == "udp_destination_port":
                    self[field_name] = match_raw["udp-destination-port"]

                elif field_name == "udp_source_port":
                    self[field_name] = match_raw["udp-source-port"]

                elif field_name == "vlan_id":
                    self[field_name] = match_raw["vlan-match"]["vlan-id"]["vlan-id"]

            except KeyError:
                continue

    def __getitem__(self, item):
        return self.field_values[item]

    def __setitem__(self, field_name, value):
        self.field_values[field_name] = value

    def __delitem__(self, field_name):
        del self.field_values[field_name]

    def keys(self):
        return self.field_values.keys()


class Match(DictMixin):
    def __getitem__(self, item):
        return self.match_field_values[item]

    def __setitem__(self, key, value):
        self.match_field_values[key] = value

    def __delitem__(self, key):
        del self.match_field_values[key]

    def keys(self):
        return self.match_field_values.keys()

    def __init__(self, match_raw=None, controller=None, flow=None, is_wildcard=True):

        self.flow = flow
        self.match_field_values = {}

        if match_raw and controller == "onos":
            self.add_element_from_onos_match_raw(match_raw)
        elif match_raw and controller == "ryu":
            self.add_element_from_ryu_match_raw(match_raw)
        elif match_raw and controller == "grpc":
            self.add_element_from_grpc_match_raw(match_raw)
        elif match_raw:
            raise NotImplemented
        elif is_wildcard:
            for field_name in field_names:
                self.match_field_values[field_name] = sys.maxsize

    def is_match_field_wildcard(self, field_name):
        return self.match_field_values[field_name] == sys.maxsize

    def add_element_from_onos_match_raw(self, match_raw):

        def get_onos_match_field(field_name, match_raw):

            for onos_field_dict in match_raw:
                if onos_field_dict["type"] == onos_field_names_mapping_reverse[field_name][0]:
                    return onos_field_dict[onos_field_names_mapping_reverse[field_name][1]]

            raise KeyError

        for field_name in field_names:

            try:
                if field_name == "in_port":
                    in_port_str = get_onos_match_field(field_name, match_raw)
                    self[field_name] = int(in_port_str)

                elif field_name == "ethernet_type":
                    eth_type_str = get_onos_match_field(field_name, match_raw)
                    self[field_name] = int(eth_type_str, 16)

                elif field_name == "ethernet_source":
                    mac_str = get_onos_match_field(field_name, match_raw)
                    mac_int = int(mac_str.replace(":", ""), 16)
                    self[field_name] = mac_int

                elif field_name == "ethernet_destination":
                    mac_str = get_onos_match_field(field_name, match_raw)
                    mac_int = int(mac_str.replace(":", ""), 16)
                    self[field_name] = mac_int

                # TODO: Add graceful handling of IP addresses
                elif field_name == "src_ip_addr":
                    ip_str = get_onos_match_field(field_name, match_raw)
                    self[field_name] = IPNetwork(ip_str)
                elif field_name == "dst_ip_addr":
                    ip_str = get_onos_match_field(field_name, match_raw)
                    self[field_name] = IPNetwork(ip_str)

                elif field_name == "ip_protocol":
                    ip_proto_str = get_onos_match_field(field_name, match_raw)
                    self[field_name] = int(ip_proto_str)

                elif field_name == "tcp_destination_port":
                    self[field_name] = int(get_onos_match_field(field_name, match_raw))

                elif field_name == "tcp_source_port":
                    self[field_name] = int(get_onos_match_field(field_name, match_raw))

                elif field_name == "udp_destination_port":
                    self[field_name] = int(get_onos_match_field(field_name, match_raw))

                elif field_name == "udp_source_port":
                    self[field_name] = int(get_onos_match_field(field_name, match_raw))

                elif field_name == "vlan_id":

                    vlan_id = get_onos_match_field(field_name, match_raw)

                    if vlan_id == 4096:
                        self[field_name] = sys.maxsize
                        self["has_vlan_tag"] = 1
                    else:
                        self[field_name] = 0x1000 + vlan_id
                        self["has_vlan_tag"] = 1

            except KeyError:
                self[field_name] = sys.maxsize

                if field_name == 'vlan_id':
                    self["has_vlan_tag"] = sys.maxsize

                continue

    def add_element_from_ryu_match_raw(self, match_raw):

        for field_name in field_names:

            try:
                if field_name == "in_port":
                    try:
                        self[field_name] = int(match_raw["in_port"])

                    except ValueError:
                        parsed_in_port = match_raw["in-port"].split(":")[2]
                        self[field_name] = int(parsed_in_port)

                elif field_name == "ethernet_type":
                    self[field_name] = int(match_raw["eth_type"])

                elif field_name == "ethernet_source":
                    mac_int = int(match_raw[u"eth_src"].replace(":", ""), 16)
                    self[field_name] = mac_int

                elif field_name == "ethernet_destination":
                    mac_int = int(match_raw[u"eth_dst"].replace(":", ""), 16)
                    self[field_name] = mac_int

                # TODO: Add graceful handling of IP addresses
                elif field_name == "src_ip_addr":
                    self[field_name] = IPNetwork(match_raw["nw_src"])
                elif field_name == "dst_ip_addr":
                    self[field_name] = IPNetwork(match_raw["nw_dst"])

                elif field_name == "ip_protocol":
                    self[field_name] = int(match_raw["nw_proto"])
                elif field_name == "tcp_destination_port":

                    if match_raw["nw_proto"] == 6:
                        self[field_name] = int(match_raw["tp_dst"])
                    else:
                        self[field_name] = match_raw["zzzz"]

                elif field_name == "tcp_source_port":

                    if match_raw["nw_proto"] == 6:
                        self[field_name] = int(match_raw["tp_src"])
                    else:
                        self[field_name] = match_raw["zzzz"]

                elif field_name == "udp_destination_port":

                    if match_raw["nw_proto"] == 17:
                        self[field_name] = int(match_raw["tp_dst"])
                    else:
                        self[field_name] = match_raw["zzzz"]

                elif field_name == "udp_source_port":

                    if match_raw["nw_proto"] == 17:
                        self[field_name] = int(match_raw["tp_src"])
                    else:
                        self[field_name] = match_raw["zzzz"]

                elif field_name == "vlan_id":

                    if match_raw[u"vlan_vid"] == "0x1000/0x1000":
                        self[field_name] = sys.maxsize
                        self["has_vlan_tag"] = 1
                    else:
                        self[field_name] = 0x1000 + int(match_raw[u"vlan_vid"])
                        self["has_vlan_tag"] = 1

            except KeyError:
                self[field_name] = sys.maxsize

                if field_name == 'vlan_id':
                    self["has_vlan_tag"] = sys.maxsize

                continue

    def add_element_from_grpc_match_raw(self, match_raw):

        for field_name in field_names:

            ryu_field_name = ryu_field_names_mapping_reverse[field_name]

            if ryu_field_name in match_raw.fields:
                self[field_name] = match_raw.fields[ryu_field_name].value
            else:
                self[field_name] = sys.maxsize

        if self[ryu_field_names_mapping["vlan_vid"]] != sys.maxsize:
            if match_raw.fields["vlan_vid"].value == 0x1000:
                self["has_vlan_tag"] = 1
            else:
                self["has_vlan_tag"] = sys.maxsize


    def generate_onos_match_raw(self, match_raw, has_vlan_tag_check):

        match_raw = []

        def get_onos_match_field_dict(field_name, val):
            match_field_dict = {"type": onos_field_names_mapping_reverse[field_name][0],
                                       onos_field_names_mapping_reverse[field_name][1]: val}
            return match_field_dict

        for field_name in field_names:

            if has_vlan_tag_check:
                if field_name == "vlan_id":
                    val = int("0x1000", 16)
                    match_raw.append(get_onos_match_field_dict(field_name, val))

            if field_name in self and self[field_name] != sys.maxsize:

                if field_name == "ethernet_source" or field_name == "ethernet_destination":

                    mac_hex_str = hex(self[field_name])[2:]
                    if len(mac_hex_str) == 11:
                        mac_hex_str = "0" + mac_hex_str
                    mac_hex_str = unicode(':'.join(s.encode('hex') for s in mac_hex_str.decode('hex')))

                    match_raw.append(get_onos_match_field_dict(field_name, mac_hex_str))

                elif field_name == "ethernet_type":
                    eth_type_str = hex(self[field_name])
                    eth_type_str = eth_type_str[0:2] + "0" + eth_type_str[2:]
                    match_raw.append(get_onos_match_field_dict(field_name, eth_type_str))
                else:
                    match_raw.append(get_onos_match_field_dict(field_name, self[field_name]))

        return match_raw

    def generate_ryu_match_raw(self, match_raw, has_vlan_tag_check=False):

        for field_name in field_names:

            if has_vlan_tag_check:
                if field_name == "vlan_id":
                    match_raw[ryu_field_names_mapping_reverse[field_name]] = "0x1000/0x1000"

            if field_name in self and self[field_name] != sys.maxsize:

                if field_name == "ethernet_source" or field_name == "ethernet_destination":

                    # print "self[field_name]:", self[field_name]
                    mac_hex_str = hex(self[field_name])[2:]
                    # print "mac_hex_str:", mac_hex_str
                    if len(mac_hex_str) == 11:
                        mac_hex_str = "0" + mac_hex_str

                    mac_hex_str = unicode(':'.join(s.encode('hex') for s in mac_hex_str.decode('hex')))
                    match_raw[ryu_field_names_mapping_reverse[field_name]] = mac_hex_str
                else:
                    match_raw[ryu_field_names_mapping_reverse[field_name]] = self[field_name]

        return match_raw

    def generate_match_raw(self, controller, match_raw, has_vlan_tag_check=False):

        if controller == "ryu":
            return self.generate_ryu_match_raw(match_raw, has_vlan_tag_check)
        elif controller == "onos":
            return self.generate_onos_match_raw(match_raw, has_vlan_tag_check)
        else:
            raise NotImplementedError
