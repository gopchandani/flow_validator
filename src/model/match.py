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

    def __init__(self, match_json, flow):

        self.match_fields = {}
        self.add_element_from_match_json(match_json, flow)

    def __getitem__(self, item):
        return self.match_fields[item]

    def __setitem__(self, key, value):
        self.match_fields[key] = value

    def __delitem__(self, key):
        del self.match_fields[key]

    def keys(self):
        return self.match_fields.keys()

    def intersect(self, in_match):

        match_intersection = Match()

        for field in self.match_fields:
            match_intersection[field] = in_match[field].intersect(self[field])
            if not match_intersection[field]:
                return None

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


class Match(DictMixin):

    def __init__(self, match_json=None, flow=None):

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

            except KeyError:
                self[field_name].add_element(0, sys.maxsize, flow)

                # Special case
                if field_name == "vlan_id":
                    self["has_vlan_tag"].add_element(0, sys.maxsize, flow)

                continue

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

def main():
    m1 = Match()
    print m1

    m2 = Match()
    m3 = m1.intersect(m2)
    print m3

if __name__ == "__main__":
    main()
