__author__ = 'Rakesh Kumar'

from netaddr import IPNetwork
from univset import univset

from UserDict import DictMixin
from match_field import MatchField2


class Match2(DictMixin):

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
            self[field_name] = MatchField2(field_name)

        if match_json:
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

        for match_field in match_json:

            if match_field == 'in-port':
                self["in_port"].add_element(int(match_json[match_field].split(":")[2]),
                                            int(match_json[match_field].split(":")[2]),
                                            flow)

            elif match_field == "ethernet-match":
                if "ethernet-type" in match_json[match_field]:
                    self["ethernet_type"].add_element(int(match_json[match_field]["ethernet-type"]["type"]),
                                                      int(match_json[match_field]["ethernet-type"]["type"]),
                                                      flow)

                if "ethernet-source" in match_json[match_field]:
                    mac_int = int(match_json[match_field]["ethernet-source"]["address"].replace(":", ""), 16)
                    self["ethernet_source"].add_element(mac_int, mac_int, flow)

                if "ethernet-destination" in match_json[match_field]:
                    mac_int = int(match_json[match_field]["ethernet-destination"]["address"].replace(":", ""), 16)
                    self["ethernet_destination"].add_element(mac_int, mac_int, flow)

            elif match_field == 'ipv4-destination':
                a = IPNetwork(match_json[match_field])
                b = int(a)
                self["dst_ip_addr"].add_element(IPNetwork(match_json[match_field]))

            elif match_field == 'ipv4-source':
                self["src_ip_addr"].add_element(IPNetwork(match_json[match_field]))

            elif match_field == "ip-match":
                if "ip-protocol" in match_json[match_field]:
                    self["ip_protocol"].add_element(int(match_json[match_field]["ip-protocol"]),
                                                    int(match_json[match_field]["ip-protocol"]),
                                                    flow)

            elif match_field == "tcp-destination-port":
                self["tcp_destination_port"].add_element(int(match_json[match_field]),
                                                         int(match_json[match_field]),
                                                         flow)

            elif match_field == "tcp-source-port":
                self["tcp_source_port"].add_element(int(match_json[match_field]),
                                                    int(match_json[match_field]),
                                                    flow)

            elif match_field == "udp-destination-port":
                self["udp_destination_port"].add_element(int(match_json[match_field]),
                                                         int(match_json[match_field]),
                                                         flow)

            elif match_field == "udp-source-port":
                self["udp_source_port"].add_element(int(match_json[match_field]),
                                                    int(match_json[match_field]),
                                                    flow)

            elif match_field == "vlan-match":
                if "vlan-id" in match_json[match_field]:
                    self["vlan_id"].add_element(int(match_json[match_field]["vlan-id"]["vlan-id"]),
                                                int(match_json[match_field]["vlan-id"]["vlan-id"]),
                                                flow)

                    self["has_vlan_tag"].add_element(1, 1, flow)

    def add_elements_from_match(self, match):

        for field_name in match:
            self[field_name].union(match[field_name])

class MatchField(object):

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
            raise Exception("Invalid type of value for MatchField: " + str(type(val)))

    def intersect(self, in_field):

        field_intersection = in_field.value_set & self.value_set
        if field_intersection:
            return MatchField(self.name, in_field.value_set & self.value_set)
        else:
            return None

    def complement(self, in_field):

        field_complement = self.value_set - in_field.value_set
        return MatchField(self.name, field_complement)

    def __str__(self):
        return str(self.name) + ": " + str(self.value_set)


class Match():

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
            self.match_fields[name] = MatchField(name, val)

    def get_field(self, name):
        return self.match_fields[name].val

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
