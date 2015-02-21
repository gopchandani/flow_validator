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


class MatchJsonParser():

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


class MatchElement(DictMixin):

    def __getitem__(self, item):
        return self.value_cache[item]

    def __setitem__(self, key, value):
        self.value_cache[key] = value

    def __delitem__(self, key):
        del self.value_cache[key]

    def keys(self):
        return self.value_cache.keys()

    def __init__(self, match_json=None, flow=None, is_wildcard=True, init_match_fields=True):

        self.value_cache = {}
        self.match_fields = {}

        # Create one IntervalTree per field.
        if init_match_fields:
            for field_name in field_names:
                self.match_fields[field_name] = IntervalTree()

        if match_json and flow:
            self.add_element_from_match_json(match_json, flow)
        elif is_wildcard:
            for field_name in field_names:
                self.set_match_field_element(field_name, is_wildcard=True)

    def set_match_field_element(self, key, value=None, flow=None, tag=None, is_wildcard=False):

        # First remove all current intervals
        prev_intervals = list(self.match_fields[key])
        for iv in prev_intervals:
            self.match_fields[key].remove(iv)

        if is_wildcard:
            self.match_fields[key].add(Interval(0, sys.maxsize, flow))
            self.value_cache[key] = sys.maxsize
        else:
            self.match_fields[key].add(Interval(value, value + 1, tag))
            self.value_cache[key] = value

    #TODO: Does not cover the cases of fragmented wildcard
    def is_field_wildcard(self, field_name):
        return Interval(0, sys.maxsize) in self.match_fields[field_name]

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

        for field_name in field_names:
            intersection_element.match_fields[field_name] = self.get_matched_tree(
                in_match_element.match_fields[field_name], self.match_fields[field_name])

            # If the resulting tree has no intervals in it, then balk:
            if not intersection_element.match_fields[field_name]:
                print "in_match:", in_match_element.match_fields[field_name], "self:", self.match_fields[field_name]
                return None

        return intersection_element

    def complement_match(self, tag):

        match_complement = Match(tag)

        for field_name in field_names:

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
                    self.set_match_field_element("has_vlan_tag", 1, flow)

            except KeyError:
                self.set_match_field_element(field_name, is_wildcard=True)
                # Special case
                if field_name == "vlan_id":
                    self.set_match_field_element("has_vlan_tag", is_wildcard=True)

                continue

    def get_orig_match_element(self, modified_fields, matching_element):

        orig_match_element = MatchElement(is_wildcard=False, init_match_fields=False)

        for field_name in field_names:
            if field_name in modified_fields:

                # If the field was modified, make it what it was (in abstract) before being modified
                orig_match_element.match_fields[field_name] = matching_element.match_fields[field_name]
            else:

                # Otherwise, just keep the field same as it was
                orig_match_element.match_fields[field_name] = self.match_fields[field_name]

        return orig_match_element

    def fix_match_element(self, modified_fields, next_port_match, matching_element):

        # Go through the fields that this match element has resulted in modifying...
        for field_name in modified_fields:

            # Construct a dummy tree from the value
            iv = Interval(int(modified_fields[field_name]), int(modified_fields[field_name]) + 1)
            it = IntervalTree()
            it.add(iv)

            # For every one of the elements in the next_port match, check
            # if you ever or check if you always
            for next_port_match_element in next_port_match.match_elements:

                x = self.get_matched_tree(it, next_port_match_element.match_fields[field_name])
                if len(x) > 0:

                    print field_name

                    # Then fix my admitted match using
                    self.match_fields[field_name] = matching_element.match_fields[field_name]


    def set_fields_with_match_json(self, match_json):

        for match_field in match_json:

            if match_field == 'in-port':
                self.set_match_field_element("in_port", int(match_json[match_field]))

            elif match_field == "ethernet-match":
                if "ethernet-type" in match_json[match_field]:
                    self.set_match_field_element("ethernet_type", int(match_json[match_field]["ethernet-type"]["type"]))

                if "ethernet-source" in match_json[match_field]:
                    self.set_match_field_element("ethernet_source", int(match_json[match_field]["ethernet-source"]["address"]))

                if "ethernet-destination" in match_json[match_field]:
                    self.set_match_field_element("ethernet_destination", int(match_json[match_field]["ethernet-destination"]["address"]))

            elif match_field == 'ipv4-destination':
                self.set_match_field_element("dst_ip_addr", IPNetwork(match_json[match_field]))

            elif match_field == 'ipv4-source':
                self.set_match_field_element("src_ip_addr", IPNetwork(match_json[match_field]))

            elif match_field == "ip-match":
                if "ip-protocol" in match_json[match_field]:
                    self.set_match_field_element("ip_protocol", int(match_json[match_field]["ip-protocol"]))

            elif match_field == "tcp-destination-port":
                self.set_match_field_element("tcp_destination_port", int(match_json[match_field]))

            elif match_field == "tcp-source-port":
                self.set_match_field_element("tcp_source_port", int(match_json[match_field]))

            elif match_field == "udp-destination-port":
                self.set_match_field_element("udp_destination_port", int(match_json[match_field]))

            elif match_field == "udp-source-port":
                self.set_match_field_element("udp_source_port", int(match_json[match_field]))

            elif match_field == "vlan-match":
                if "vlan-id" in match_json[match_field]:
                    self.set_match_field_element("vlan_id", int(match_json[match_field]["vlan-id"]["vlan-id"]))
                    self.set_match_field_element("has_vlan_tag", int(True))


    def generate_match_json(self, match):

        if "in_port" in self and self["in_port"] != sys.maxsize:
            match["in-port"] = self["in_port"]

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

        match["ethernet-match"] = ethernet_match

        if "src_ip_addr" in self and self["src_ip_addr"] != sys.maxsize:
            match["ipv4-source"] = self["src_ip_addr"]

        if "dst_ip_addr" in self and self["dst_ip_addr"] != sys.maxsize:
            match["ipv4-destination"] = self["dst_ip_addr"]

        if ("tcp_destination_port" in self and self["tcp_destination_port"] != sys.maxsize) or \
                ("tcp_source_port" in self and self["tcp_source_port"] != sys.maxsize):
            self["ip_protocol"] = 6
            match["ip-match"] = {"ip-protocol": self["ip_protocol"]}

            if "tcp_destination_port" in self and self["tcp_destination_port"] != sys.maxsize:
                match["tcp-destination-port"] = self["tcp_destination_port"]

            if "tcp_source_port" in self and self["tcp_source_port"] != sys.maxsize:
                match["tcp-source-port"] = self["tcp_source_port"]

        if ("udp_destination_port" in self and self["udp_destination_port"] != sys.maxsize) or \
                ("udp_source_port" in self and self["udp_source_port"] != sys.maxsize):
            self["ip_protocol"] = 17
            match["ip-match"] = {"ip-protocol": self["ip_protocol"]}

            if "udp_destination_port" in self and self["udp_destination_port"] != sys.maxsize:
                match["udp-destination-port"]= self["udp_destination_port"]

            if "udp_source_port" in self and self["udp_source_port"] != sys.maxsize:
                match["udp-source-port"] = self["udp_source_port"]

        if "vlan_id" in self and self["vlan_id"] != sys.maxsize:
            vlan_match = {}
            vlan_match["vlan-id"] = {"vlan-id": self["vlan_id"], "vlan-id-present": True}
            match["vlan-match"] = vlan_match

        return match

class Match():

    def __init__(self, tag=None, init_wildcard=False):

        self.tag = tag
        self.match_elements = []

        # If initialized as wildcard, add one to the list
        if init_wildcard:
            self.match_elements.append(MatchElement(is_wildcard=True))

    def is_empty(self):
        return len(self.match_elements) == 0

    def set_field(self, key, value=None, match_json=None, is_wildcard=False):

        if key and value:
            for me in self.match_elements:
                me.set_match_field_element(key, value)

        elif is_wildcard:
            for me in self.match_elements:
                me.set_match_field_element(key, is_wildcard=True)

        elif match_json:
            for me in self.match_elements:
                me.set_fields_with_match_json(match_json)


    def intersect(self, in_match):
        im = Match()
        for e1 in self.match_elements:
            for e2 in in_match.match_elements:
                ei = e1.intersect(e2)
                if ei:
                    im.match_elements.append(ei)
        return im

    def union(self, in_match):

        self.match_elements.extend(in_match.match_elements)

        return self




    def get_orig_match(self, modified_fields, matching_element):

        orig_match = Match()
        for me in self.match_elements:
            orig_match.match_elements.append(me.get_orig_match_element(modified_fields, matching_element))
        return orig_match

    def fix_match(self, modified_fields, next_port_match, matching_element):

        for me in self.match_elements:
            me.fix_match_element(modified_fields, next_port_match, matching_element)

    def is_field_wildcard(self, field_name):
        retval = True

        for me in self.match_elements:
            retval = me.is_field_wildcard(field_name)
            if not retval:
                break

        return retval

    #TODO: Very hacky.
    # Assumes that there is only a single element and for that element, in the given field,
    # there is only a single interval present

    def get_field_val(self, field_name):
        return list(self.match_elements[0].match_fields[field_name].all_intervals)[0].begin

def main():
    m1 = Match()
    print m1

    m2 = Match()
    m3 = m1.intersect(m2)
    print m3

if __name__ == "__main__":
    main()