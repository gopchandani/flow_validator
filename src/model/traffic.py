__author__ = 'Rakesh Kumar'

import sys
from match import MatchElement, field_names
from external.intervaltree import Interval, IntervalTree

class TrafficElement():

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

    def __init__(self, match_json=None, controller=None, flow=None, is_wildcard=True, init_match_fields=True, traffic=None):

        self.traffic = traffic
        self.port = None
        self.succ_match_element = None
        self.pred_match_elements = []
        self.written_field_modifications = {}

        self.match_fields = {}
        self.has_vlan_tag = False

        # Create one IntervalTree per field.
        if init_match_fields:
            for field_name in field_names:
                self.match_fields[field_name] = IntervalTree()

        if match_json and flow and controller == "odl":
            self.add_element_from_odl_match_json(match_json, flow)
        elif match_json and flow and controller == "ryu":
            self.add_element_from_ryu_match_json(match_json, flow)
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

        elif is_wildcard:
            self.match_fields[key].add(Interval(0, sys.maxsize, flow))

        else:
            if isinstance(value, IPNetwork):
                self.match_fields[key].add(Interval(value.first, value.last + 1))
            else:
                self.match_fields[key].add(Interval(value, value + 1))

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

        return matched_tree

    def intersect(self, in_match_element):

        intersection_element = TrafficElement()

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

    def get_complement_match_elements(self):

        complement_match_elements = []

        for field_name in field_names:

            #If the field is not a wildcard, then chop it from the wildcard initialized Traffic
            if not (Interval(0, sys.maxsize) in self.match_fields[field_name]):
                me = TrafficElement(is_wildcard=True)

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

    def add_element_from_odl_match_json(self, match_json, flow):

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

    def add_element_from_ryu_match_json(self, match_json, flow):

        for field_name in field_names:

            try:
                if field_name == "in_port":
                    try:
                        self.set_match_field_element(field_name, int(match_json["in_port"]), flow)

                    except ValueError:
                        parsed_in_port = match_json["in-port"].split(":")[2]
                        self.set_match_field_element(field_name, int(parsed_in_port), flow)

                elif field_name == "ethernet_type":
                    self.set_match_field_element(field_name, int(match_json["dl_type"]), flow)

                elif field_name == "ethernet_source":
                    mac_int = int(match_json[u"dl_src"].replace(":", ""), 16)
                    self.set_match_field_element(field_name, mac_int, flow)

                elif field_name == "ethernet_destination":
                    mac_int = int(match_json[u"dl_dst"].replace(":", ""), 16)
                    self.set_match_field_element(field_name, mac_int, flow)

                #TODO: Add graceful handling of IP addresses
                elif field_name == "src_ip_addr":
                    self.set_match_field_element(field_name, IPNetwork(match_json["nw_src"]))
                elif field_name == "dst_ip_addr":
                    self.set_match_field_element(field_name, IPNetwork(match_json["nw_dst"]))

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
                    self.set_match_field_element(field_name, int(match_json[u"dl_vlan"]), flow)

            except KeyError:
                self.set_match_field_element(field_name, is_wildcard=True)
                continue


    def get_orig_match_element(self, field_modifications=None):

        if field_modifications:
            mf = field_modifications
        else:
            mf = self.written_field_modifications

        orig_match_element = TrafficElement(is_wildcard=False, init_match_fields=False)

        for field_name in field_names:

            # If the field is modified in the Traffic as it passes through a rule,
            # The original traffic that comes at the front of that rule is computed as follows:
            # If the field was not modified, then it is left as-is, no harm done
            # If the field is modified however, it is left as-is too, unless it is modified to the exact value
            # as it is contained in the traffic

            if field_name in mf:

                #TODO: Do this more properly ground up from the parser
                field_val = int(mf[field_name][1])
                value_tree = IntervalTree()
                value_tree.add(Interval(field_val, field_val + 1))

                intersection = self.get_matched_tree(value_tree, self.match_fields[field_name])

                if intersection:
                    orig_match_element.match_fields[field_name] = mf[field_name][0]
                else:
                     orig_match_element.match_fields[field_name] = self.match_fields[field_name]

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

class Traffic():

    def __init__(self, init_wildcard=False):

        self.match_elements = []

        # If initialized as wildcard, add one to the list
        if init_wildcard:
            self.match_elements.append(TrafficElement(is_wildcard=True))

    def add_match_elements(self, me_list):
        for me in me_list:
            self.match_elements.append(me)
            me.traffic = self

    def is_empty(self):
        return len(self.match_elements) == 0

    def set_field(self, key, value=None, match_json=None, is_wildcard=False, exception=False):

        if key and value and exception:
            for me in self.match_elements:
                me.set_match_field_element(key, value, exception=True)

        elif key and value:
            for me in self.match_elements:
                me.set_match_field_element(key, value)

        elif is_wildcard:
            for me in self.match_elements:
                me.set_match_field_element(key, is_wildcard=True)

        elif match_json:
            for me in self.match_elements:
                me.set_fields_with_match_json(match_json)

    def is_subset_me(self, in_me):

        is_subset = False
        for self_me in self.match_elements:
            if self_me.is_subset(in_me):
                is_subset = True
                break

        return is_subset

    def is_redundant_me(self, in_me):

        is_redundant = False
        for self_me in self.match_elements:
            if self_me.is_subset(in_me) and self_me.succ_match_element == in_me.succ_match_element:
                is_redundant = True
                break

        return is_redundant

    def intersect(self, in_traffic):
        im = Traffic()
        for e_in in in_traffic.match_elements:
            for e_self in self.match_elements:
                ei = e_self.intersect(e_in)
                if ei:

                    # Check to see if this intersection can be expressed as subset of any of the previous
                    # me's that are already collected
                    is_subset = im.is_subset_me(ei)

                    # If so, no need to add this one to the mix
                    if is_subset:
                        continue

                    # Add this and do the necessary book-keeping...
                    ei.traffic = im
                    im.match_elements.append(ei)

                    ei.written_field_modifications.update(e_in.written_field_modifications)

                    # Establish that the resulting ei is based on e_in
                    ei.succ_match_element = e_in
                    e_in.pred_match_elements.append(ei)

        return im

    def union(self, in_traffic):

        for union_me in in_traffic.match_elements:

            # Check to see if this needs to be added at all
            if self.is_redundant_me(union_me):
                continue

            union_me.traffic = self
            self.match_elements.append(union_me)

        return self

    def pipe_welding(self, now_admitted_match):

        # Check if this existing_me can be taken even partially by any of the candidates
        # TODO: This does not handle left-over cases when parts of the existing_me are taken by multiple candidate_me

        #print "pipe_welding has:", len(self.match_elements), "existing match elements to take care of..."

        for existing_me in self.match_elements:
            existing_me_welded = False
            for candidate_me in now_admitted_match.match_elements:

                if candidate_me.is_subset(existing_me):
                    existing_me.written_field_modifications.update(candidate_me.written_field_modifications)
                    existing_me.succ_match_element = candidate_me.succ_match_element
                    existing_me_welded = True
                    break

            # If none of the candidate_me took existing_me:
            #Delete everybody who dependent on existing_me, the whole chain...
            if not existing_me_welded:
                existing_me.succ_match_element = None

    def get_orig_traffic(self, modified_fields=None):

        orig_traffic = Traffic()
        for me in self.match_elements:
            orig_me = me.get_orig_match_element(modified_fields)
            orig_me.traffic = orig_traffic
            orig_traffic.match_elements.append(orig_me)
        return orig_traffic

    def set_port(self, port):
        for me in self.match_elements:
            me.port = port

    def set_succ_match_element(self, succ_match_element):
        for me in self.match_elements:
            me.succ_match_element = succ_match_element
            succ_match_element.pred_match_elements.append(me)

    def is_field_wildcard(self, field_name):
        retval = True

        for me in self.match_elements:
            retval = me.is_field_wildcard(field_name)
            if not retval:
                break

        return retval

    def print_port_paths(self):

        for me in self.match_elements:
            print me.get_port_path_str()


def main():
    m1 = Traffic()
    print m1

    m2 = Traffic()
    m3 = m1.intersect(m2)
    print m3

if __name__ == "__main__":
    main()