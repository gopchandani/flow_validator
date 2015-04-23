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
              "vlan_id"]

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

    def __str__(self):
        if self.port:
            return str(id(self)) + "@" + self.port.port_id
        else:
            return str(id(self)) + "@NONE"

    def get_port_path_str(self):

        port_path_str = self.port.port_id + "(" + str(id(self)) + ")"
        trav = self.succ_match_element

        while trav != None:
            port_path_str += (" -> " + trav.port.port_id + "(" + str(id(trav)) + ")")
            trav = trav.succ_match_element

        return port_path_str

    def __init__(self, match_json=None, flow=None, is_wildcard=True, init_match_fields=True, traffic=None):

        self.traffic = traffic
        self.port = None
        self.edge_data_key = None
        self.succ_match_element = None
        self.pred_match_elements = []
        self.written_field_modifications = {}
        self.causing_match_element = None

        self.value_cache = {}
        self.match_fields = {}
        self.has_vlan_tag = False

        # Create one IntervalTree per field.
        if init_match_fields:
            for field_name in field_names:
                self.match_fields[field_name] = IntervalTree()

        if match_json and flow:
            self.add_element_from_match_json(match_json, flow)
        elif is_wildcard:
            for field_name in field_names:
                self.set_match_field_element(field_name, is_wildcard=True)

    def set_match_field_element(self, key, value=None, flow=None, is_wildcard=False, exception=False):

        # First remove all current intervals
        prev_intervals = list(self.match_fields[key])
        for iv in prev_intervals:
            self.match_fields[key].remove(iv)

        if exception:
            self.match_fields[key].add(Interval(0, value, flow))
            self.match_fields[key].add(Interval(value + 1, sys.maxsize, flow))
            self.value_cache[key] = sys.maxsize

        elif is_wildcard:
            self.match_fields[key].add(Interval(0, sys.maxsize, flow))
            self.value_cache[key] = sys.maxsize

        else:
            self.match_fields[key].add(Interval(value, value + 1))
            self.value_cache[key] = value

    #TODO: Does not cover the cases of fragmented wildcard
    def is_field_wildcard(self, field_name):
        return Interval(0, sys.maxsize) in self.match_fields[field_name]

    def get_matched_tree(self, tree1, tree2):

        matched_tree = IntervalTree()
        for iv in tree1:
            for matched_iv in tree2.search(iv.begin, iv.end):

                # Take the smaller interval of the two and put it in the matched_tree
                if matched_iv.contains_interval(iv):
                    matched_tree.add(iv)

                elif iv.contains_interval(matched_iv):
                    matched_tree.add(matched_iv)

                elif iv.overlaps(matched_iv.begin, matched_iv.end):
                    overlapping_interval = Interval(max(matched_iv.begin, iv.begin), min(matched_iv.end, iv.end))
                    matched_tree.append(overlapping_interval)
                else:
                    raise Exception("Probably should never get here")

                #TODO: Take the smallest overlap between two intervals and put it in

        return matched_tree

    def intersect(self, in_match_element):

        intersection_element = MatchElement()

        for field_name in field_names:
            intersection_element.match_fields[field_name] = self.get_matched_tree(
                in_match_element.match_fields[field_name], self.match_fields[field_name])

            # If the resulting tree has no intervals in it, then balk:
            if not intersection_element.match_fields[field_name]:
                #print field_name, \
                #    "self:", self.match_fields[field_name], \
                #    "in_match:", in_match_element.match_fields[field_name]
                return None

        return intersection_element

    def pipe_welding(self, candidate_me):

        new_me = MatchElement()

        for field_name in field_names:
            new_me.match_fields[field_name] = self.get_matched_tree(
                candidate_me.match_fields[field_name], self.match_fields[field_name])

            # If the resulting tree has no intervals in it, then balk:
            if not new_me.match_fields[field_name]:
                #print field_name, \
                #    "self:", self.match_fields[field_name], \
                #    "candidate_me:", candidate_me.match_fields[field_name]
                return None

        new_me.port = self.port
        new_me.causing_match_element = self.causing_match_element
        new_me.written_field_modifications.update(candidate_me.written_field_modifications)

        # -- Set up what self depended on, in new_me

        # The resulting new_me would have same successor as candidate_me
        new_me.succ_match_element = candidate_me.succ_match_element

        # Remove self from the successor's predecessor list, if it exists
        while self in new_me.succ_match_element.pred_match_elements:
            new_me.succ_match_element.pred_match_elements.remove(self)

        # Add new_me to successor's predecessor list
        new_me.succ_match_element.pred_match_elements.append(new_me)

        # -- Set up what depended on self, in new_me

        # new_me's predecessors are all of self's predecessors
        new_me.pred_match_elements = self.pred_match_elements

        # new_me would have to tell its predecessors that they depend on new_me now
        for me in new_me.pred_match_elements:
            me.succ_match_element = new_me

        return new_me

    def remove_with_predecessors(self):

#        print "remove_with_predecessors at:", self.port, "--", self.get_port_path_str()

        #If there are any predecessors, go take care of them first
#        print "At:", self
#        for pred in self.pred_match_elements:
#           print "-", pred

        while self.pred_match_elements:
            pred = self.pred_match_elements.pop()
            #print "At:", self, "Going to predecessor:", pred
            pred.remove_with_predecessors()

        self.succ_match_element = None

        # Remove this one from its traffic's list of Match Elements
        if self in self.traffic.match_elements:
            self.traffic.match_elements.remove(self)
        else:
            pass
            #print "Removing something that is already removed."
            #raise Exception("Removing something that is already removed.")

    def get_complement_match_elements(self):

        complement_match_elements = []

        for field_name in field_names:

            #If the field is not a wildcard, then chop it from the wildcard initialized Traffic
            if not (Interval(0, sys.maxsize) in self.match_fields[field_name]):
                me = MatchElement(is_wildcard=True)

                # Chop out each interval from me[field_name]
                for interval in self.match_fields[field_name]:
                    me.match_fields[field_name].chop(interval.begin, interval.end)

                complement_match_elements.append(me)

        return complement_match_elements


    # A is_subset of B if A - B == NullSet
    # A is in_match_element
    # B here is self

    def is_subset(self, in_match_element):

        # find B'
        complement_match_elements = self.get_complement_match_elements()

        # Intersect in_match_element with B' to get A-B by doing A Int B'
        diff_match_elements = []
        for cme in complement_match_elements:
            i = in_match_element.intersect(cme)
            if i:
                diff_match_elements.append(i)

        # Return True/False based on if there was anything found in A Int B'
        if diff_match_elements:
            return False
        else:
            return True


    def add_element_from_match_json(self, match_json, flow):

        for field_name in field_names:

            try:
                if field_name == "in_port":
                    try:
                        self.set_match_field_element(field_name, int(match_json["in-port"]), flow)
                    except ValueError:
                        parsed_in_port = match_json["in-port"].split(":")[2]
                        self.set_match_field_element(field_name, int(parsed_in_port), flow)

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

            except KeyError:
                self.set_match_field_element(field_name, is_wildcard=True)
                continue

    def get_orig_match_element(self, modified_fields=None, matching_element=None):

        if modified_fields:
            mf = modified_fields
        else:
            mf = self.written_field_modifications

        if matching_element:
            me = matching_element
        else:
            me = self.causing_match_element

        orig_match_element = MatchElement(is_wildcard=False, init_match_fields=False)

        for field_name in field_names:
            if field_name in mf:
                # If the field was modified, make it what it was (in abstract) before being modified
                orig_match_element.match_fields[field_name] = me.match_fields[field_name]
            else:
                # Otherwise, just keep the field same as it was
                orig_match_element.match_fields[field_name] = self.match_fields[field_name]

        # Accumulate field modifications
        orig_match_element.written_field_modifications.update(self.written_field_modifications)

        # This newly minted ME depends on the succ_match_element
        orig_match_element.succ_match_element = self.succ_match_element

        # This also means that succ_match_element.pred_match_elements also need to carry around orig_match_element
        if self.succ_match_element:
            self.succ_match_element.pred_match_elements.append(orig_match_element)

        # Copy these from self
        orig_match_element.port = self.port
        orig_match_element.causing_match_element = self.causing_match_element
        orig_match_element.pred_match_elements = self.pred_match_elements

        return orig_match_element

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
