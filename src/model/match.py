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
              "vlan_id"]

ryu_field_names_mapping = {"in_port": "in_port",
                           "eth_type": "ethernet_type",
                           "eth_src": "ethernet_source",
                           "eth_dst":"ethernet_destination",
                           "nw_src": "src_ip_addr",
                           "nw_dst":"dst_ip_addr",
                           "nw_proto": "ip_protocol",
                           "tcp_dst": "tcp_destination_port",
                           "tcp_src": "tcp_source_port",
                           "udp_dst": "udp_destination_port",
                           "udp_src": "udp_source_port",
                           "vlan_vid": "vlan_id"}

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
                                   "vlan_id": "dl_vlan"}


class OdlMatchJsonParser():

    def __init__(self, match_json=None):
        self.field_values = {}
        self._parse(match_json)

    def _parse(self, match_json):

        for field_name in field_names:

            try:
                if field_name == "in_port":
                     self[field_name] = match_json["in-port"]

                elif field_name == "ethernet_type":
                    self[field_name] = match_json["ethernet-match"]["ethernet-type"]["type"]

                elif field_name == "ethernet_source":
                     self[field_name] = match_json["ethernet-match"]["ethernet-source"]["address"]

                elif field_name == "ethernet_destination":
                    self[field_name] = match_json["ethernet-match"]["ethernet-destination"]["address"]

                elif field_name == "src_ip_addr":
                    self[field_name] =  match_json["src_ip_addr"]

                elif field_name == "dst_ip_addr":
                    self[field_name] =  match_json["dst_ip_addr"]

                elif field_name == "ip_protocol":
                    self[field_name] = match_json["ip-match"]["ip-protocol"]

                elif field_name == "tcp_destination_port":
                    self[field_name] = match_json["tcp-destination-port"]

                elif field_name == "tcp_source_port":
                    self[field_name] = match_json["tcp-source-port"]

                elif field_name == "udp_destination_port":
                    self[field_name] = match_json["udp-destination-port"]

                elif field_name == "udp_source_port":
                    self[field_name] = match_json["udp-source-port"]

                elif field_name == "vlan_id":
                    self[field_name] = match_json["vlan-match"]["vlan-id"]["vlan-id"]

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

    def __init__(self, match_json=None, controller=None, flow=None, is_wildcard=True):

        self.flow = flow
        self.match_field_values = {}

        if match_json and controller == "odl":
            self.add_element_from_odl_match_json(match_json)
        elif match_json and controller == "ryu":
            self.add_element_from_ryu_match_json(match_json)
        elif match_json and controller == "sel":
            self.add_element_from_sel_match_json(match_json)
        elif is_wildcard:
            for field_name in field_names:
                self.match_field_values[field_name] = sys.maxsize

    def is_field_wildcard(self, field_name):
        return self.match_field_values[field_name] == sys.maxsize

    def add_element_from_odl_match_json(self, match_json):

        for field_name in field_names:
            try:
                if field_name == "in_port":
                    try:
                        self[field_name] = int(match_json["in-port"])
                    except ValueError:
                        parsed_in_port = match_json["in-port"].split(":")[2]
                        self[field_name] = int(parsed_in_port)

                elif field_name == "ethernet_type":
                    self[field_name] = int(match_json["ethernet-match"]["ethernet-type"]["type"])
                elif field_name == "ethernet_source":
                    mac_int = int(match_json["ethernet-match"]["ethernet-source"]["address"].replace(":", ""), 16)
                    self[field_name] = mac_int

                elif field_name == "ethernet_destination":
                    mac_int = int(match_json["ethernet-match"]["ethernet-destination"]["address"].replace(":", ""), 16)
                    self[field_name] = mac_int

                #TODO: Add graceful handling of IP addresses
                elif field_name == "src_ip_addr":
                    self[field_name] = IPNetwork(match_json["src_ip_addr"])
                elif field_name == "dst_ip_addr":
                    self[field_name] = IPNetwork(match_json["dst_ip_addr"])

                elif field_name == "ip_protocol":
                    self[field_name] = int(match_json["ip-match"]["ip-protocol"])
                elif field_name == "tcp_destination_port":
                    self[field_name] = int(match_json["tcp-destination-port"])
                elif field_name == "tcp_source_port":
                    self[field_name] = int(match_json["tcp-source-port"])
                elif field_name == "udp_destination_port":
                    self[field_name] = int(match_json["udp-destination-port"])
                elif field_name == "udp_source_port":
                    self[field_name] = int(match_json["udp-source-port"])
                elif field_name == "vlan_id":
                    self[field_name] = int(match_json["vlan-match"]["vlan-id"]["vlan-id"])

            except KeyError:
                self[field_name] = sys.maxsize
                continue

    def add_element_from_sel_match_json(self, match_json):

        for field_name in field_names:
            try:
                if field_name == "in_port":
                    self[field_name] = int(match_json["inPort"])

                elif field_name == "ethernet_type":
                    self[field_name] = int(match_json["ethType"])

                elif field_name == "ethernet_source":
                    mac_int = int(match_json["ethSrc"].replace(":", ""), 16)
                    self[field_name] = mac_int

                elif field_name == "ethernet_destination":
                    mac_int = int(match_json["ethDst"].replace(":", ""), 16)
                    self[field_name] = mac_int

                #TODO: Add graceful handling of IP addresses
                elif field_name == "src_ip_addr":
                    self[field_name] = IPNetwork(match_json["ipv4Src"])
                elif field_name == "dst_ip_addr":
                    self[field_name] = IPNetwork(match_json["ipv4Dst"])

                elif field_name == "ip_protocol":
                    self[field_name] = int(match_json["ipProto"])
                elif field_name == "tcp_destination_port":
                    self[field_name] = int(match_json["tcpDst"])
                elif field_name == "tcp_source_port":
                    self[field_name] = int(match_json["tcpSrc"])
                elif field_name == "udp_destination_port":
                    self[field_name] = int(match_json["udpDst"])
                elif field_name == "udp_source_port":
                    self[field_name] = int(match_json["udpSrc"])
                elif field_name == "vlan_id":
                    self[field_name] = int(match_json[u"vlanVid"])

            except (AttributeError, TypeError, ValueError):
                self[field_name] = sys.maxsize
                continue


    def add_element_from_ryu_match_json(self, match_json):

        for field_name in field_names:

            try:
                if field_name == "in_port":
                    try:
                        self[field_name] = int(match_json["in_port"])

                    except ValueError:
                        parsed_in_port = match_json["in-port"].split(":")[2]
                        self[field_name] = int(parsed_in_port)

                elif field_name == "ethernet_type":
                    self[field_name] = int(match_json["dl_type"])

                elif field_name == "ethernet_source":
                    mac_int = int(match_json[u"dl_src"].replace(":", ""), 16)
                    self[field_name] = mac_int

                elif field_name == "ethernet_destination":
                    mac_int = int(match_json[u"dl_dst"].replace(":", ""), 16)
                    self[field_name] = mac_int

                #TODO: Add graceful handling of IP addresses
                elif field_name == "src_ip_addr":
                    self[field_name] = IPNetwork(match_json["nw_src"])
                elif field_name == "dst_ip_addr":
                    self[field_name] = IPNetwork(match_json["nw_dst"])

                elif field_name == "ip_protocol":
                    self[field_name] = int(match_json["ip-match"]["ip-protocol"])
                elif field_name == "tcp_destination_port":
                    self[field_name] = int(match_json["tcp-destination-port"])
                elif field_name == "tcp_source_port":
                    self[field_name] = int(match_json["tcp-source-port"])
                elif field_name == "udp_destination_port":
                    self[field_name] = int(match_json["udp-destination-port"])
                elif field_name == "udp_source_port":
                    self[field_name] = int(match_json["udp-source-port"])
                elif field_name == "vlan_id":
                    self[field_name] = int(match_json[u"dl_vlan"])

            except KeyError:
                self[field_name] = sys.maxsize
                continue

    def set_fields_with_match_json(self, match_json):

        for match_field in match_json:

            if match_field == 'in-port':
                self["in_port"] = int(match_json[match_field])

            elif match_field == "ethernet-match":
                if "ethernet-type" in match_json[match_field]:
                    self["ethernet_type"] = int(match_json[match_field]["ethernet-type"]["type"])

                if "ethernet-source" in match_json[match_field]:
                    self["ethernet_source"] = int(match_json[match_field]["ethernet-source"]["address"])

                if "ethernet-destination" in match_json[match_field]:
                    self["ethernet_destination"] = int(match_json[match_field]["ethernet-destination"]["address"])

            elif match_field == 'ipv4-destination':
                self["dst_ip_addr"] = IPNetwork(match_json[match_field])

            elif match_field == 'ipv4-source':
                self["src_ip_addr"] = IPNetwork(match_json[match_field])

            elif match_field == "ip-match":
                if "ip-protocol" in match_json[match_field]:
                    self["ip_protocol"] = int(match_json[match_field]["ip-protocol"])

            elif match_field == "tcp-destination-port":
                self["tcp_destination_port"] = int(match_json[match_field])

            elif match_field == "tcp-source-port":
                self["tcp_source_port"] = int(match_json[match_field])

            elif match_field == "udp-destination-port":
                self["udp_destination_port"] = int(match_json[match_field])

            elif match_field == "udp-source-port":
                self["udp_source_port"] = int(match_json[match_field])

            elif match_field == "vlan-match":
                if "vlan-id" in match_json[match_field]:
                    self["vlan_id"] = int(match_json[match_field]["vlan-id"]["vlan-id"])

    def generate_odl_match_json(self, match_json):

        if "in_port" in self and self["in_port"] != sys.maxsize:
            match_json["in-port"] = self["in_port"]

        ethernet_match = {}

        if "ethernet_type" in self and self["ethernet_type"] != sys.maxsize:
            ethernet_match["ethernet-type"] = {"type": self["ethernet_type"]}

        if "ethernet_source" in self and self["ethernet_source"] != sys.maxsize:

            mac_int = self["ethernet_source"]
            mac_hex_str = hex(mac_int)[2:]
            mac_hex_str = unicode(':'.join(s.encode('hex') for s in mac_hex_str.decode('hex')))

            ethernet_match["ethernet-source"] = {"address": mac_hex_str}

        if "ethernet_destination" in self and self["ethernet_destination"] != sys.maxsize:

            mac_int = self["ethernet_destination"]
            mac_hex_str = format(mac_int, "012x")
            mac_hex_str = unicode(':'.join(s.encode('hex') for s in mac_hex_str.decode('hex')))

            ethernet_match["ethernet-destination"] = {"address": mac_hex_str}

        match_json["ethernet-match"] = ethernet_match

        if "src_ip_addr" in self and self["src_ip_addr"] != sys.maxsize:
            match_json["ipv4-source"] = self["src_ip_addr"]

        if "dst_ip_addr" in self and self["dst_ip_addr"] != sys.maxsize:
            match_json["ipv4-destination"] = self["dst_ip_addr"]

        if ("tcp_destination_port" in self and self["tcp_destination_port"] != sys.maxsize) or \
                ("tcp_source_port" in self and self["tcp_source_port"] != sys.maxsize):
            self["ip_protocol"] = 6
            match_json["ip-match"] = {"ip-protocol": self["ip_protocol"]}

            if "tcp_destination_port" in self and self["tcp_destination_port"] != sys.maxsize:
                match_json["tcp-destination-port"] = self["tcp_destination_port"]

            if "tcp_source_port" in self and self["tcp_source_port"] != sys.maxsize:
                match_json["tcp-source-port"] = self["tcp_source_port"]

        if ("udp_destination_port" in self and self["udp_destination_port"] != sys.maxsize) or \
                ("udp_source_port" in self and self["udp_source_port"] != sys.maxsize):
            self["ip_protocol"] = 17
            match_json["ip-match"] = {"ip-protocol": self["ip_protocol"]}

            if "udp_destination_port" in self and self["udp_destination_port"] != sys.maxsize:
                match_json["udp-destination-port"]= self["udp_destination_port"]

            if "udp_source_port" in self and self["udp_source_port"] != sys.maxsize:
                match_json["udp-source-port"] = self["udp_source_port"]

        if "vlan_id" in self and self["vlan_id"] != sys.maxsize:
            vlan_match = {}
            vlan_match["vlan-id"] = {"vlan-id": self["vlan_id"], "vlan-id-present": True}
            match_json["vlan-match"] = vlan_match

        return match_json


    def generate_sel_match_json(self, match):
        if "in_port" in self and self["in_port"] != sys.maxsize:
            # TODO(abhilash) check what does SEL want in case of port_in;
            # it errors out if you let the port number (self["port_in"]) pass
            # through as value. IPv4 keeps it quiet, but I am not sure if it
            # wants that.
            match.__setattr__("in_port", str(self["in_port"]))

        if "ethernet_type" in self and self["ethernet_type"] != sys.maxsize:
            # Picked up the values from
            # http://www.iana.org/assignments/ieee-802-numbers/ieee-802-numbers.xhtml
            match.__setattr__("eth_type", str(self["ethernet_type"]))


        if "ethernet_source" in self and self["ethernet_source"] != sys.maxsize:

            mac_int = self["ethernet_source"]
            mac_hex_str = hex(mac_int)[2:]
            mac_hex_str = unicode(':'.join(s.encode('hex') for s in mac_hex_str.decode('hex')))

            match.__setattr__("eth_src",mac_hex_str)

        if "ethernet_destination" in self and self["ethernet_destination"] != sys.maxsize:

            mac_int = self["ethernet_destination"]
            mac_hex_str = format(mac_int, "012x")
            mac_hex_str = unicode(':'.join(s.encode('hex') for s in mac_hex_str.decode('hex')))

            match.__setattr__("eth_dst", mac_hex_str)

        if "src_ip_addr" in self and self["src_ip_addr"] != sys.maxsize:
            match.__setattr__("ipv4_src", self["src_ip_addr"])

        if "dst_ip_addr" in self and self["dst_ip_addr"] != sys.maxsize:
            match.__setattr__("ipv4_dst", self["dst_ip_addr"])

        if ("tcp_destination_port" in self and self["tcp_destination_port"] != sys.maxsize) or \
                ("tcp_source_port" in self and self["tcp_source_port"] != sys.maxsize):
            self["ip_protocol"] = 6
            match.__setattr__("ip_proto", str(self["ip_protocol"]))

        if "tcp_destination_port" in self and self["tcp_destination_port"] != sys.maxsize:
            match.__setattr__("tcp_dst", self["tcp_destination_port"])

        if "tcp_source_port" in self and self["tcp_source_port"] != sys.maxsize:
            match.__setattr__("tcp_src", self["tcp_source_port"])

        if "udp_destination_port" in self and self["udp_destination_port"] != sys.maxsize:
            match.__setattr__("udp_dst", self["udp_destination_port"])

        if "udp_source_port" in self and self["udp_source_port"] != sys.maxsize:
            match.__setattr__("udp_src", self["udp_source_port"])

        if "vlan_id" in self and self["vlan_id"] != sys.maxsize:
           match.__setattr__("vlan_id", str(self["vlan_id"]))

        return match

    def generate_ryu_match_json(self, match_json):

        for field_name in field_names:

            if field_name in self and self[field_name] != sys.maxsize:

                if field_name == "ethernet_source" or field_name == "ethernet_destination":

                    #print "self[field_name]:", self[field_name]
                    mac_hex_str = hex(self[field_name])[2:]
                    #print "mac_hex_str:", mac_hex_str
                    if len(mac_hex_str) == 11:
                        mac_hex_str = "0" + mac_hex_str

                    mac_hex_str = unicode(':'.join(s.encode('hex') for s in mac_hex_str.decode('hex')))
                    match_json[ryu_field_names_mapping_reverse[field_name]] = mac_hex_str
                else:
                    match_json[ryu_field_names_mapping_reverse[field_name]] = self[field_name]

        return match_json

    def generate_match_json(self, controller, match_json):

        if controller == "ryu":
            return self.generate_ryu_match_json(match_json)
        elif controller == "odl":
            return self.generate_odl_match_json(match_json)
        elif controller == "sel":
            return self.generate_sel_match_json(match_json)
        else:
            raise NotImplementedError