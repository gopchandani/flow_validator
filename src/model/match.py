__author__ = 'Rakesh Kumar'


import sys

from netaddr import IPNetwork
from univset import univset

from UserDict import DictMixin
from match_field import MatchField, MatchFieldElement

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

class MatchElement(DictMixin):

    def __init__(self, match_json=None, flow=None):

        self.match_fields = {}

        if match_json is not None and flow:
            self.add_element_from_match_json(match_json, flow)

    def __getitem__(self, item):
        return self.match_fields[item]

    def __setitem__(self, key, value):
        self.match_fields[key] = value

    def set_match_field_element(self, key, value, tag=None):
        self.match_fields[key] = MatchFieldElement(value, value, tag)

    def __delitem__(self, key):
        del self.match_fields[key]

    def keys(self):
        return self.match_fields.keys()

    def complement(self, in_match):

        match_complement = Match()

        for field in self.match_fields:
            complement = in_match[field].complement(self[field])

        return match_complement

    def intersect(self, in_match):

        match_intersection = Match()

        for field in self.match_fields:
            intersection = in_match[field].intersect(self[field])
            if not intersection:
                return None
            else:
                match_intersection[field] = MatchField(field)

                if in_match.get_field(field):

                    match_intersection[field]["intersection"] = MatchFieldElement(in_match.get_field(field),
                                                          in_match.get_field(field),
                                                          "intersection")
                else:
                    match_intersection[field]["intersection"] = MatchFieldElement(self[field]._low,
                                                                                  self[field]._high,
                                                                                  "intersection")


        return match_intersection

    def add_element_from_match_json(self, match_json, flow):

        for field_name in field_names:

            try:
                if field_name == "in_port":

                    self[field_name] = MatchFieldElement(int(match_json["in-port"]),
                                                 int(match_json["in-port"]),
                                                 flow)

                    #self[field_name] = MatchFieldElement(int(match_json["in-port"].split(":")[2]),
                    #                            int(match_json["in-port"].split(":")[2]),
                    #                            flow)

                elif field_name == "ethernet_type":
                    self[field_name] = MatchFieldElement(int(match_json["ethernet-match"]["ethernet-type"]["type"]),
                                                 int(match_json["ethernet-match"]["ethernet-type"]["type"]),
                                                 flow)

                elif field_name == "ethernet_source":
                    mac_int = int(match_json["ethernet-match"]["ethernet-source"]["address"].replace(":", ""), 16)
                    self[field_name] = MatchFieldElement(mac_int, mac_int, flow)

                elif field_name == "ethernet_destination":
                    mac_int = int(match_json["ethernet-match"]["ethernet-destination"]["address"].replace(":", ""), 16)
                    self[field_name] = MatchFieldElement(mac_int, mac_int, flow)

                #TODO: Add graceful handling of IP addresses
                elif field_name == "src_ip_addr":
                    self[field_name] = MatchFieldElement(IPNetwork(match_json["src_ip_addr"]))

                elif field_name == "dst_ip_addr":
                    self[field_name] = MatchFieldElement(IPNetwork(match_json["dst_ip_addr"]))

                elif field_name == "ip_protocol":
                    self[field_name] = MatchFieldElement(int(match_json["ip-match"]["ip-protocol"]),
                                                 int(match_json["ip-match"]["ip-protocol"]),
                                                 flow)

                elif field_name == "tcp_destination_port":
                    self[field_name] = MatchFieldElement(int(match_json["tcp-destination-port"]),
                                                 int(match_json["tcp-destination-port"]),
                                                 flow)

                elif field_name == "tcp_source_port":
                    self[field_name] = MatchFieldElement(int(match_json["tcp-source-port"]),
                                                 int(match_json["tcp-source-port"]),
                                                 flow)

                elif field_name == "udp_destination_port":
                    self[field_name] = MatchFieldElement(int(match_json["udp-destination-port"]),
                                                 int(match_json["udp-destination-port"]),
                                                 flow)
                elif field_name == "udp_source_port":
                    self[field_name] = MatchFieldElement(int(match_json["udp-source-port"]),
                                                 int(match_json["udp-source-port"]),
                                                 flow)
                elif field_name == "vlan_id":
                    self["vlan_id"] = MatchFieldElement(int(match_json["vlan-match"]["vlan-id"]["vlan-id"]),
                                                int(match_json["vlan-match"]["vlan-id"]["vlan-id"]),
                                                flow)

                    self["has_vlan_tag"] = MatchFieldElement(1, 1, flow)

            except KeyError:
                self[field_name] = MatchFieldElement(0, sys.maxsize, flow)

                # Special case
                if field_name == "vlan_id":
                    self["has_vlan_tag"] = MatchFieldElement(0, sys.maxsize, flow)

                continue

    def generate_match_json(self, match):

        if "in_port" in self and self["in_port"].high != sys.maxsize:
            match["in-port"] = self["in_port"].low

        ethernet_match = {}

        if "ethernet_type" in self and self["ethernet_type"].high != sys.maxsize:
            ethernet_match["ethernet-type"] = {"type": self["ethernet_type"].low}

        if "ethernet_source" in self and self["ethernet_source"].high != sys.maxsize:

            mac_int = self["ethernet_source"].low
            mac_hex_str = hex(mac_int)[2:]
            mac_hex_str = unicode(':'.join(s.encode('hex') for s in mac_hex_str.decode('hex')))

            ethernet_match["ethernet-source"] = {"address": mac_hex_str}

        if "ethernet_destination" in self and self["ethernet_destination"].high != sys.maxsize:

            mac_int = self["ethernet_destination"].low
            mac_hex_str = hex(mac_int)[2:]
            mac_hex_str = unicode(':'.join(s.encode('hex') for s in mac_hex_str.decode('hex')))

            ethernet_match["ethernet-destination"] = {"address": mac_hex_str}

        match["ethernet-match"] = ethernet_match

        if "src_ip_addr" in self and self["src_ip_addr"].high != sys.maxsize:
            match["ipv4-source"] = self["src_ip_addr"].low

        if "dst_ip_addr" in self and self["dst_ip_addr"].high != sys.maxsize:
            match["ipv4-destination"] = self["dst_ip_addr"].low

        if ("tcp_destination_port" in self and self["tcp_destination_port"].high != sys.maxsize) or \
                ("tcp_source_port" in self and self["tcp_source_port"].high != sys.maxsize):
            self["ip_protocol"].low = 6
            match["ip-match"] = {"ip-protocol": self["ip_protocol"].low}

            if "tcp_destination_port" in self and self["tcp_destination_port"].high != sys.maxsize:
                match["tcp-destination-port"] = self["tcp_destination_port"].low

            if "tcp_source_port" in self and self["tcp_source_port"].high != sys.maxsize:
                match["tcp-source-port"] = self["tcp_source_port"].low

        if ("udp_destination_port" in self and self["udp_destination_port"].high != sys.maxsize) or \
                ("udp_source_port" in self and self["udp_source_port"].high != sys.maxsize):
            self["ip_protocol"].low = 17
            match["ip-match"] = {"ip-protocol": self["ip_protocol"].low}

            if "udp_destination_port" in self and self["udp_destination_port"].high != sys.maxsize:
                match["udp-destination-port"]= self["udp_destination_port"].low

            if "udp_source_port" in self and self["udp_source_port"].high != sys.maxsize:
                match["udp-source-port"] = self["udp_source_port"].low

        if "vlan_id" in self and self["vlan_id"].high != sys.maxsize:
            vlan_match = {}
            vlan_match["vlan-id"] = {"vlan-id": self["vlan_id"].low, "vlan-id-present": True}
            match["vlan-match"] = vlan_match

        return match


class Match(DictMixin):

    def __str__(self):
        ret_str = "Match: "
        for f in self.match_fields:
            ret_str += "\n" + str(self.match_fields[f])

        return ret_str

    def __init__(self, tag=None):

        self.match_fields = {}
        self.tag = tag

        for field_name in field_names:
            self[field_name] = MatchField(field_name)
            self[field_name][tag] = MatchFieldElement(0, sys.maxsize, tag)

    def __delitem__(self, key):
        del self.match_fields[key]
    
    def keys(self):
        return self.match_fields.keys()

    def __getitem__(self, item):
        return self.match_fields[item]

    def __setitem__(self, key, value):
        self.match_fields[key] = value

    def set_field(self, key, value):
        self[key] = MatchField(key)
        self[key][self.tag] = MatchFieldElement(value, value, self.tag)

    def get_field(self, key):
        field = self.match_fields[key]

        # If the field is not a wildcard, return a value, otherwise none
        if field.pos_list and field.pos_list[len(field.pos_list) - 1] != sys.maxsize:
            return field.pos_list[0]
        else:
             return None

    def set_fields_with_match_json(self, match_json):

        for match_field in match_json:

            if match_field == 'in-port':
                self.set_field("in_port", int(match_json[match_field]))

            elif match_field == "ethernet-match":
                if "ethernet-type" in match_json[match_field]:
                    self.set_field("ethernet_type", int(match_json[match_field]["ethernet-type"]["type"]))

                if "ethernet-source" in match_json[match_field]:
                    self.set_field("ethernet_source", int(match_json[match_field]["ethernet-source"]["address"]))

                if "ethernet-destination" in match_json[match_field]:
                    self.set_field("ethernet_destination", int(match_json[match_field]["ethernet-destination"]["address"]))

            elif match_field == 'ipv4-destination':
                self.set_field("dst_ip_addr", IPNetwork(match_json[match_field]))

            elif match_field == 'ipv4-source':
                self.set_field("src_ip_addr", IPNetwork(match_json[match_field]))

            elif match_field == "ip-match":
                if "ip-protocol" in match_json[match_field]:
                    self.set_field("ip_protocol", int(match_json[match_field]["ip-protocol"]))

            elif match_field == "tcp-destination-port":
                self.set_field("tcp_destination_port", int(match_json[match_field]))

            elif match_field == "tcp-source-port":
                self.set_field("tcp_source_port", int(match_json[match_field]))

            elif match_field == "udp-destination-port":
                self.set_field("udp_destination_port", int(match_json[match_field]))

            elif match_field == "udp-source-port":
                self.set_field("udp_source_port", int(match_json[match_field]))

            elif match_field == "vlan-match":
                if "vlan-id" in match_json[match_field]:
                    self.set_field("vlan_id", int(match_json[match_field]["vlan-id"]["vlan-id"]))
                    self.set_field("has_vlan_tag", int(True))

def main():
    m1 = Match()
    print m1

    m2 = Match()
    m3 = m1.intersect(m2)
    print m3

if __name__ == "__main__":
    main()
