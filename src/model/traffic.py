__author__ = 'Rakesh Kumar'

import sys

from netaddr import IPNetwork
from match import Match, field_names
from external.intervaltree import Interval, IntervalTree

class TrafficElement():

    def __init__(self, init_match=None, init_field_wildcard=False):

        self.traffic = None
        self.port = None
        self.succ_traffic_element = None
        self.pred_traffic_elements = []
        self.written_field_modifications = {}

        self.match_fields = {}
        self.has_vlan_tag = False

        # If a match has been provided to initialize with
        if init_match:
            for field_name in field_names:
                self.match_fields[field_name] = IntervalTree()

                if init_match[field_name] == sys.maxsize:
                    self.set_match_field_element(field_name, is_wildcard=True)
                else:
                    self.set_match_field_element(field_name, init_match[field_name])

        # Create one IntervalTree per field and put the wildcard interval in it
        if init_field_wildcard:
            for field_name in field_names:
                self.match_fields[field_name] = IntervalTree()
                self.set_match_field_element(field_name, is_wildcard=True)

    def __str__(self):
        if self.port:
            return str(id(self)) + "@" + self.port.port_id
        else:
            return str(id(self)) + "@NONE"

    def get_port_path_str(self):

        port_path_str = self.port.port_id + "(" + str(id(self)) + ")"
        trav = self.succ_traffic_element

        while trav != None:
            port_path_str += (" -> " + trav.port.port_id + "(" + str(id(trav)) + ")")
            trav = trav.succ_traffic_element

        return port_path_str
    
    def set_match_field_element(self, key, value=None, is_wildcard=False, exception=False):

        # First remove all current intervals
        prev_intervals = list(self.match_fields[key])
        for iv in prev_intervals:
            self.match_fields[key].remove(iv)

        if exception:
            self.match_fields[key].add(Interval(0, value))
            self.match_fields[key].add(Interval(value + 1, sys.maxsize))

        elif is_wildcard:
            self.match_fields[key].add(Interval(0, sys.maxsize))

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

    def intersect(self, in_traffic_element):

        intersection_element = TrafficElement()

        for field_name in field_names:
            intersection_element.match_fields[field_name] = self.get_matched_tree(
                in_traffic_element.match_fields[field_name], self.match_fields[field_name])

            # If the resulting tree has no intervals in it, then balk:
            if not intersection_element.match_fields[field_name]:
                #print field_name, \
                #    "self:", self.match_fields[field_name], \
                #    "in_match:", in_traffic_element.match_fields[field_name]
                return None

        return intersection_element

    def get_complement_traffic_elements(self):

        complement_traffic_elements = []
        for field_name in field_names:

            # If the field is not a wildcard, then chop it from the wildcard initialized Traffic
            if not (Interval(0, sys.maxsize) in self.match_fields[field_name]):
                te = TrafficElement(init_field_wildcard=True)

                # Chop out each interval from te[field_name]
                for interval in self.match_fields[field_name]:
                    te.match_fields[field_name].chop(interval.begin, interval.end)

                complement_traffic_elements.append(te)

        return complement_traffic_elements


    # A is_subset of B if A - B == NullSet
    # A is in_traffic_element
    # B here is self

    def is_subset(self, in_traffic_element):

        # find B'
        complement_traffic_elements = self.get_complement_traffic_elements()

        # Intersect in_traffic_element with B' to get A-B by doing A Int B'
        diff_traffic_elements = []
        for cme in complement_traffic_elements:
            i = in_traffic_element.intersect(cme)
            if i:
                diff_traffic_elements.append(i)

        # Return True/False based on if there was anything found in A Int B'
        if diff_traffic_elements:
            return False
        else:
            return True

    def get_orig_traffic_element(self, field_modifications=None):

        if field_modifications:
            mf = field_modifications
        else:
            mf = self.written_field_modifications

        orig_traffic_element = TrafficElement()

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
                    orig_traffic_element.match_fields[field_name] = mf[field_name][0]
                else:
                     orig_traffic_element.match_fields[field_name] = self.match_fields[field_name]

            else:
                # Otherwise, just keep the field same as it was
                orig_traffic_element.match_fields[field_name] = self.match_fields[field_name]

        # Accumulate field modifications
        orig_traffic_element.written_field_modifications.update(self.written_field_modifications)

        # This newly minted ME depends on the succ_traffic_element
        orig_traffic_element.succ_traffic_element = self.succ_traffic_element

        # This also means that succ_traffic_element.pred_traffic_elements also need to carry around orig_traffic_element
        if self.succ_traffic_element:
            self.succ_traffic_element.pred_traffic_elements.append(orig_traffic_element)

        # Copy these from self
        orig_traffic_element.port = self.port
        orig_traffic_element.pred_traffic_elements = self.pred_traffic_elements

        return orig_traffic_element

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

        self.traffic_elements = []

        # If initialized as wildcard, add one to the list
        if init_wildcard:
            self.traffic_elements.append(TrafficElement(init_field_wildcard=True))

    def add_traffic_elements(self, te_list):
        for te in te_list:
            self.traffic_elements.append(te)
            te.traffic = self

    def is_empty(self):
        return len(self.traffic_elements) == 0

    def set_field(self, key, value=None, match_json=None, is_wildcard=False, exception=False):

        if key and value and exception:
            for te in self.traffic_elements:
                te.set_match_field_element(key, value, exception=True)

        elif key and value:
            for te in self.traffic_elements:
                te.set_match_field_element(key, value)

        elif is_wildcard:
            for te in self.traffic_elements:
                te.set_match_field_element(key, is_wildcard=True)

        elif match_json:
            for te in self.traffic_elements:
                te.set_fields_with_match_json(match_json)

    def is_subset_te(self, in_te):

        is_subset = False
        for self_te in self.traffic_elements:
            if self_te.is_subset(in_te):
                is_subset = True
                break

        return is_subset

    def is_redundant_te(self, in_te):

        is_redundant = False
        for self_te in self.traffic_elements:
            if self_te.is_subset(in_te) and self_te.succ_traffic_element == in_te.succ_traffic_element:
                is_redundant = True
                break

        return is_redundant

    def intersect(self, in_traffic):
        traffic_intersection = Traffic()
        for e_in in in_traffic.traffic_elements:
            for e_self in self.traffic_elements:
                ei = e_self.intersect(e_in)
                if ei:

                    # Check to see if this intersection can be expressed as subset of any of the previous
                    # te's that are already collected
                    is_subset = traffic_intersection.is_subset_te(ei)

                    # If so, no need to add this one to the mix
                    if is_subset:
                        continue

                    # Add this and do the necessary book-keeping...
                    ei.traffic = traffic_intersection
                    traffic_intersection.traffic_elements.append(ei)

                    ei.written_field_modifications.update(e_in.written_field_modifications)

                    # Establish that the resulting ei is based on e_in
                    ei.succ_traffic_element = e_in
                    e_in.pred_traffic_elements.append(ei)

        return traffic_intersection

    def union(self, in_traffic):

        for union_te in in_traffic.traffic_elements:

            # Check to see if this needs to be added at all
            if self.is_redundant_te(union_te):
                continue

            union_te.traffic = self
            self.traffic_elements.append(union_te)

        return self

    def pipe_welding(self, now_admitted_match):

        # Check if this existing_te can be taken even partially by any of the candidates
        # TODO: This does not handle left-over cases when parts of the existing_te are taken by multiple candidate_te

        #print "pipe_welding has:", len(self.traffic_elements), "existing match elements to take care of..."

        for existing_te in self.traffic_elements:
            existing_te_welded = False
            for candidate_te in now_admitted_match.traffic_elements:

                if candidate_te.is_subset(existing_te):
                    existing_te.written_field_modifications.update(candidate_te.written_field_modifications)
                    existing_te.succ_traffic_element = candidate_te.succ_traffic_element
                    existing_te_welded = True
                    break

            # If none of the candidate_te took existing_te:
            #Delete everybody who dependent on existing_te, the whole chain...
            if not existing_te_welded:
                existing_te.succ_traffic_element = None

    def get_orig_traffic(self, modified_fields=None):

        orig_traffic = Traffic()
        for te in self.traffic_elements:
            orig_te = te.get_orig_traffic_element(modified_fields)
            orig_te.traffic = orig_traffic
            orig_traffic.traffic_elements.append(orig_te)
        return orig_traffic

    def set_port(self, port):
        for te in self.traffic_elements:
            te.port = port

    def set_succ_traffic_element(self, succ_traffic_element):
        for te in self.traffic_elements:
            te.succ_traffic_element = succ_traffic_element
            succ_traffic_element.pred_traffic_elements.append(te)

    def is_field_wildcard(self, field_name):
        retval = True

        for te in self.traffic_elements:
            retval = te.is_field_wildcard(field_name)
            if not retval:
                break

        return retval

    def print_port_paths(self):

        for te in self.traffic_elements:
            print te.get_port_path_str()


def main():
    m1 = Traffic()
    print m1

    m2 = Traffic()
    m3 = m1.intersect(m2)
    print m3

if __name__ == "__main__":
    main()