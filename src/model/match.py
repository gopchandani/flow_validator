__author__ = 'Rakesh Kumar'


import sys

from netaddr import IPNetwork
from univset import univset

from UserDict import DictMixin
from match_field import MatchField



class Match(DictMixin):

    def __init__(self, match_json=None, flow=None):

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

        self.match_fields = {}
        for field_name in field_names:
            self[field_name] = MatchField(field_name)

        if match_json != None:
            self.add_elements_from_match_json(match_json, flow)

    def __getitem__(self, item):
        return self.match_fields[item]
    
    def __setitem__(self, key, value):
        self.match_fields[key] = value
    
    def __delitem__(self, key):
        del self.match_fields[key]
    
    def keys(self):
        return self.match_fields.keys()

    def add_elements_from_match_json(self, match_json, flow):

        for field_name in self.keys():

            try:
                if field_name == "in_port":

                    self[field_name].add_element(int(match_json["in-port"]),
                                                 int(match_json["in-port"]),
                                                 flow)

                    #self[field_name].add_element(int(match_json["in-port"].split(":")[2]),
                    #                            int(match_json["in-port"].split(":")[2]),
                    #                            flow)

                elif field_name == "ethernet_type":
                    self[field_name].add_element(int(match_json["ethernet-match"]["ethernet-type"]["type"]),
                                                 int(match_json["ethernet-match"]["ethernet-type"]["type"]),
                                                 flow)

                elif field_name == "ethernet_source":
                    mac_int = int(match_json["ethernet-match"]["ethernet-source"]["address"].replace(":", ""), 16)
                    self[field_name].add_element(mac_int, mac_int, flow)

                elif field_name == "ethernet_destination":
                    mac_int = int(match_json["ethernet-match"]["ethernet-destination"]["address"].replace(":", ""), 16)
                    self[field_name].add_element(mac_int, mac_int, flow)

                elif field_name == "src_ip_addr":
                    self[field_name].add_element(IPNetwork(match_json["src_ip_addr"]))

                elif field_name == "dst_ip_addr":
                    self[field_name].add_element(IPNetwork(match_json["dst_ip_addr"]))

                elif field_name == "ip_protocol":
                    self[field_name].add_element(int(match_json["ip-match"]["ip-protocol"]),
                                                 int(match_json["ip-match"]["ip-protocol"]),
                                                 flow)

                elif field_name == "tcp_destination_port":
                    self[field_name].add_element(int(match_json["tcp-destination-port"]),
                                                 int(match_json["tcp-destination-port"]),
                                                 flow)

                elif field_name == "tcp_source_port":
                    self[field_name].add_element(int(match_json["tcp-source-port"]),
                                                 int(match_json["tcp-source-port"]),
                                                 flow)

                elif field_name == "udp_destination_port":
                    self[field_name].add_element(int(match_json["udp-destination-port"]),
                                                 int(match_json["udp-destination-port"]),
                                                 flow)
                elif field_name == "udp_source_port":
                    self[field_name].add_element(int(match_json["udp-source-port"]),
                                                 int(match_json["udp-source-port"]),
                                                 flow)
                elif field_name == "vlan_id":
                    self["vlan_id"].add_element(int(match_json["vlan-match"]["vlan-id"]["vlan-id"]),
                                                int(match_json["vlan-match"]["vlan-id"]["vlan-id"]),
                                                flow)

                    self["has_vlan_tag"].add_element(1, 1, flow)

                elif field_name == "has_vlan_tag" and "vlan-match" in match_json:
                    pass

            except KeyError:
                self[field_name].add_element(0, sys.maxsize, flow)
                continue

    #TODO:
    def add_elements_from_match(self, in_match):

        for field_name in in_match:
            self[field_name].union(in_match[field_name])

    def intersect(self, in_match):

        match_intersection = Match()
        for field in self.match_fields:
            match_intersection[field] = self[field].intersect(in_match[field])
            if not match_intersection[field]:
                return None

        return match_intersection

class MatchField2(object):

    def __init__(self, name, val):

        self.name = name
        self.set_field_value(val)

    def set_field_value(self, val):

        if isinstance(val, int):
            self.value_set = set([val])
        elif isinstance(val, univset):
            self.value_set = val
        elif isinstance(val, set):
            self.value_set = val
        else:
            raise Exception("Invalid type of value for MatchField2: " + str(type(val)))

    def get_field_value(self):

        if isinstance(self.value_set, univset):
            return univset()
        else:
            a = self.value_set.pop()
            self.value_set.add(a)
            return a

    def intersect(self, in_field):

        field_intersection = in_field.value_set & self.value_set
        if field_intersection:
            return MatchField2(self.name, in_field.value_set & self.value_set)
        else:
            return None

    def complement(self, in_field):

        field_complement = self.value_set - in_field.value_set
        return MatchField2(self.name, field_complement)

    def __str__(self):
        return str(self.name) + ": " + str(self.value_set)


class Match2():

    def __init__(self, match_json=None):
        
        self.match_fields = {}

        self.set_field("in_port", univset())
        self.set_field("ethernet_type", univset())
        self.set_field("ethernet_source", univset())
        self.set_field("ethernet_destination", univset())
        self.set_field("src_ip_addr", univset())
        self.set_field("dst_ip_addr", univset())
        self.set_field("ip_protocol", univset())
        self.set_field("tcp_destination_port", univset())
        self.set_field("tcp_source_port", univset())
        self.set_field("udp_destination_port", univset())
        self.set_field("udp_source_port", univset())
        self.set_field("vlan_id", univset())
        self.set_field("has_vlan_tag", univset())

        if match_json:
            self.set_fields_with_match_json(match_json)

    def __str__(self):
        return ", ".join([str(field) for field in self.match_fields.values()])

    def set_field(self, name, val):
        if name in self.match_fields:
            self.match_fields[name].set_field_value(val)
        else:
            self.match_fields[name] = MatchField2(name, val)

    def get_field(self, name):
        return self.match_fields[name].get_field_value()

    def set_fields_with_match_json(self, match_json):

        for match_field in match_json:

            if match_field == 'in-port':
                self.set_field("in_port", int(match_json[match_field].split(":")[2]))

            elif match_field == "ethernet-match":
                if "ethernet-type" in match_json[match_field]:
                    self.set_field("ethernet_type", int(match_json[match_field]["ethernet-type"]["type"]))

                if "ethernet-source" in match_json[match_field]:
                    mac_int = int(match_json[match_field]["ethernet-source"]["address"].replace(":", ""), 16)
                    self.set_field("ethernet_source", mac_int)

                if "ethernet-destination" in match_json[match_field]:
                    mac_int = int(match_json[match_field]["ethernet-destination"]["address"].replace(":", ""), 16)
                    self.set_field("ethernet_destination", mac_int)

            elif match_field == 'ipv4-destination':
                self.set_field("dst_ip_addr", IPNetwork(match_json[match_field]))

            elif match_field == 'ipv4-source':
                self.set_field("src_ip_addr", IPNetwork(match_json[match_field]))

            elif match_field == "ip-match":
                if "ip-protocol" in match_json[match_field]:
                    self.set_field("ip_protocol", str(match_json[match_field]["ip-protocol"]))
                    
            elif match_field == "tcp-destination-port":
                self.set_field("tcp_destination_port", str(match_json[match_field]))

            elif match_field == "tcp-source-port":
                self.set_field("tcp_source_port", str(match_json[match_field]))

            elif match_field == "udp-destination-port":
                self.set_field("udp_destination_port", str(match_json[match_field]))

            elif match_field == "udp-source-port":
                self.set_field("udp_source_port", str(match_json[match_field]))

            elif match_field == "vlan-match":
                if "vlan-id" in match_json[match_field]:
                    self.set_field("vlan_id", match_json[match_field]["vlan-id"]["vlan-id"])
                    self.set_field("has_vlan_tag", 1)


    def generate_match_json(self, match):
        if self.get_field("in_port") != univset():
            match["in-port"] = self.get_field("in_port")

        ethernet_match = {}

        if self.get_field("ethernet_type") != univset():
            ethernet_match["ethernet-type"] = {"type": self.get_field("ethernet_type")}

        if self.get_field("ethernet_source") != univset():
            ethernet_match["ethernet-source"] = {"address": self.get_field("ethernet_source")}

        if self.get_field("ethernet_destination") != univset():
            ethernet_match["ethernet-destination"] = {"address": self.get_field("ethernet_destination")}

        match["ethernet-match"] = ethernet_match

        if self.get_field("src_ip_addr") != univset():
            match["ipv4-source"] = self.get_field("src_ip_addr")

        if self.get_field("dst_ip_addr") != univset():
            match["ipv4-destination"] = self.get_field("dst_ip_addr")

        if self.get_field("tcp_destination_port") != univset() or self.get_field("tcp_source_port") != univset():
            self.set_field("ip_protocol", 6)
            match["ip-match"] = {"ip-protocol": self.get_field("ip_protocol")}

            if self.get_field("tcp_destination_port") != univset():
                match["tcp-destination-port"] = self.get_field("tcp_destination_port")

            if self.get_field("tcp_source_port") != univset():
                match["tcp-source-port"] = self.get_field("tcp_source_port")

        if self.get_field("udp_destination_port") != univset() or self.get_field("udp_source_port") != univset():
            self.set_field("ip_protocol", 17)
            match["ip-match"] = {"ip-protocol": self.get_field("ip_protocol")}

            if self.get_field("udp_destination_port") != univset():
                match["udp-destination-port"]= self.get_field("udp_destination_port")

            if self.get_field("udp_source_port") != univset():
                match["udp-source-port"] = self.get_field("udp_source_port")

        if self.get_field("vlan_id") != univset():
            vlan_match = {}
            vlan_match["vlan-id"] = {"vlan-id": self.get_field("vlan_id"), "vlan-id-present": True}
            match["vlan-match"] = vlan_match

        return match

    def intersect(self, in_match):

        match_intersection = Match()
        for field in self.match_fields:
            field_intersection = self.match_fields[field].intersect(in_match.match_fields[field])
            if field_intersection:
                match_intersection.match_fields[field] = field_intersection
            else:
                return None

        return match_intersection

    def complement(self, in_match):
        match_complement = Match()

        for field in self.match_fields:
            field_complement = self.match_fields[field].complement(in_match.match_fields[field])
            if field_complement:
                match_complement.match_fields[field] = field_complement
            else:
                return None

        return match_complement

def main():
    m1 = Match()
    print m1

    m2 = Match()
    m3 = m1.intersect(m2)
    print m3

if __name__ == "__main__":
    main()
