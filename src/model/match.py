__author__ = 'Rakesh Kumar'


import sys

from netaddr import IPNetwork
from UserDict import DictMixin
from external.intervaltree import Interval, IntervalTree

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


class MatchElement():

    def __init__(self, match_json=None, flow=None, is_wildcard=True):

        self.match_fields = {}

        # Create one IntervalTree per field.
        for field_name in field_names:
            self.match_fields[field_name] = IntervalTree()

        if match_json and flow:
            self.add_element_from_match_json(match_json, flow)
        else:
            for field_name in field_names:
                self.set_match_field_element(field_name, is_wildcard=True)

    def set_match_field_element(self, key, value=None, flow=None, tag=None, is_wildcard=False):

        # First remove all current intervals
        prev_intervals = list(self.match_fields[key])
        for iv in prev_intervals:
            self.match_fields[key].remove(iv)

        if is_wildcard:
            self.match_fields[key].add(Interval(0, sys.maxsize, flow))
        else:
            self.match_fields[key].add(Interval(value, value + 1, tag))

    def get_matched_tree(self, tree1, tree2):

        matched_tree = IntervalTree()
        for iv in tree1:
            for matched_iv in tree2.search(iv.begin, iv.end):

                #Take the smaller interval of the two and put it in the matched_tree
                if matched_iv.contains_interval(iv):
                    matched_tree.add(iv)
                elif iv.contains_interval(matched_iv):
                    matched_tree.add(matched_iv)

        return matched_tree

    def intersect(self, in_match_element):

        intersection_element = MatchElement()

        for field_name in self.match_fields:
            intersection_element.match_fields[field_name] = self.get_matched_tree(
                in_match_element.match_fields[field_name], self.match_fields[field_name])

            # If the resulting tree has no intervals in it, then balk:
            if not intersection_element.match_fields[field_name]:
                return None

        return intersection_element

    def complement_match(self, tag):

        match_complement = Match(tag)

        for field_name in self.match_fields:

            #If the field is not a wildcard, then chop it from the wildcard initialized Match
            if not (Interval(0, sys.maxsize) in self.match_fields[field_name]):
                me = MatchElement(is_wildcard=True)

                # Chop out each interval from me[field_name]
                for interval in self.match_fields[field_name]:
                    me.match_fields[field_name].chop(interval.begin, interval.end)

                match_complement.match_elements.append(me)

        return match_complement

    def add_element_from_match_json(self, match_json, flow):

        for field_name in field_names:

            try:
                if field_name == "in_port":
                     self.set_match_field_element(field_name, int(match_json["in-port"]), flow)

                elif field_name == "ethernet_type":
                    self.set_match_field_element(field_name, int(match_json["ethernet-match"]["ethernet-type"]["type"]), flow)
                elif field_name == "ethernet_source":
                    mac_int = int(match_json["ethernet-match"]["ethernet-source"]["address"].replace(":", ""), 16)
                    self.set_match_field_element(field_name, mac_int, flow)

                elif field_name == "ethernet_destination":
                    mac_int = int(match_json["ethernet-match"]["ethernet-destination"]["address"].replace(":", ""), 16)
                    self.set_match_field_element(field_name, mac_int, flow)

                #TODO: Add graceful handling of IP addresses
                elif field_name == "src_ip_addr":
                    self.set_match_field_element(field_name, IPNetwork(match_json["src_ip_addr"]))
                elif field_name == "dst_ip_addr":
                    self.set_match_field_element(field_name, IPNetwork(match_json["dst_ip_addr"]))

                elif field_name == "ip_protocol":
                    self.set_match_field_element(field_name, int(match_json["ip-match"]["ip-protocol"]), flow)
                elif field_name == "tcp_destination_port":
                    self.set_match_field_element(field_name, int(match_json["tcp-destination-port"]), flow)
                elif field_name == "tcp_source_port":
                    self.set_match_field_element(field_name, int(match_json["tcp-source-port"]), flow)
                elif field_name == "udp_destination_port":
                    self.set_match_field_element(field_name, int(match_json["udp-destination-port"]), flow)
                elif field_name == "udp_source_port":
                    self.set_match_field_element(field_name, int(match_json["udp-source-port"]), flow)

                elif field_name == "vlan_id":
                    self.set_match_field_element(field_name, int(match_json["vlan-match"]["vlan-id"]["vlan-id"]), flow)
                    self.set_match_field_element(field_name, 1, flow)

            except KeyError:
                self.set_match_field_element(field_name, is_wildcard=True)
                # Special case
                if field_name == "vlan_id":
                    self.set_match_field_element(field_name, is_wildcard=True)

                continue

    def generate_match_json(self, match):

        if "in_port" in self and self["in_port"].end != sys.maxsize:
            match["in-port"] = self["in_port"].begin

        ethernet_match = {}

        if "ethernet_type" in self and self["ethernet_type"].end != sys.maxsize:
            ethernet_match["ethernet-type"] = {"type": self["ethernet_type"].begin}

        if "ethernet_source" in self and self["ethernet_source"].end != sys.maxsize:

            mac_int = self["ethernet_source"].begin
            mac_hex_str = hex(mac_int)[2:]
            mac_hex_str = unicode(':'.join(s.encode('hex') for s in mac_hex_str.decode('hex')))

            ethernet_match["ethernet-source"] = {"address": mac_hex_str}

        if "ethernet_destination" in self and self["ethernet_destination"].end != sys.maxsize:

            mac_int = self["ethernet_destination"].begin
            mac_hex_str = hex(mac_int)[2:]
            mac_hex_str = unicode(':'.join(s.encode('hex') for s in mac_hex_str.decode('hex')))

            ethernet_match["ethernet-destination"] = {"address": mac_hex_str}

        match["ethernet-match"] = ethernet_match

        if "src_ip_addr" in self and self["src_ip_addr"].end != sys.maxsize:
            match["ipv4-source"] = self["src_ip_addr"].begin

        if "dst_ip_addr" in self and self["dst_ip_addr"].end != sys.maxsize:
            match["ipv4-destination"] = self["dst_ip_addr"].begin

        if ("tcp_destination_port" in self and self["tcp_destination_port"].end != sys.maxsize) or \
                ("tcp_source_port" in self and self["tcp_source_port"].end != sys.maxsize):
            self["ip_protocol"].begin = 6
            match["ip-match"] = {"ip-protocol": self["ip_protocol"].begin}

            if "tcp_destination_port" in self and self["tcp_destination_port"].end != sys.maxsize:
                match["tcp-destination-port"] = self["tcp_destination_port"].begin

            if "tcp_source_port" in self and self["tcp_source_port"].end != sys.maxsize:
                match["tcp-source-port"] = self["tcp_source_port"].begin

        if ("udp_destination_port" in self and self["udp_destination_port"].end != sys.maxsize) or \
                ("udp_source_port" in self and self["udp_source_port"].end != sys.maxsize):
            self["ip_protocol"].begin = 17
            match["ip-match"] = {"ip-protocol": self["ip_protocol"].begin}

            if "udp_destination_port" in self and self["udp_destination_port"].end != sys.maxsize:
                match["udp-destination-port"]= self["udp_destination_port"].begin

            if "udp_source_port" in self and self["udp_source_port"].end != sys.maxsize:
                match["udp-source-port"] = self["udp_source_port"].begin

        if "vlan_id" in self and self["vlan_id"].end != sys.maxsize:
            vlan_match = {}
            vlan_match["vlan-id"] = {"vlan-id": self["vlan_id"].begin, "vlan-id-present": True}
            match["vlan-match"] = vlan_match

        return match

class Match():

    def __init__(self, tag=None, init_wildcard=False):

        self.tag = tag
        self.match_elements = []

        # If initialized as wildcard, add one to the list
        if init_wildcard:
            self.match_elements.append(MatchElement(is_wildcard=True))

    def has_empty_field(self):
        raise Exception("Implement has_empty_field")

    def set_field(self, key, value):
        for me in self.match_elements:
            me.set_match_field_element(key, value)

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

    def intersect(self, in_match):
        im = Match()
        for e1 in self.match_elements:
            for e2 in in_match.match_elements:
                ei = e1.intersect(e2)
                if ei:
                    im.match_elements.append(ei)
        return im

def main():
    m1 = Match()
    print m1

    m2 = Match()
    m3 = m1.intersect(m2)
    print m3

if __name__ == "__main__":
    main()

    #

    #
    # def get_matched_tree(self, tree, iv):
    #
    #     matched_tree = IntervalTree()
    #     for matched_interval in tree.search(iv.begin, iv.end):
    #
    #         #Take the smaller interval of the two and put it in the matched_tree
    #         if matched_interval.contains_point(iv):
    #             matched_tree.add(iv)
    #         elif iv.contains_point(matched_interval):
    #             matched_tree.add(matched_interval)
    #
    #     return matched_tree