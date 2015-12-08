__author__ = 'Rakesh Kumar'

import sys

from netaddr import IPNetwork
from match import Match, field_names
from external.intervaltree import Interval, IntervalTree

class TrafficElement():

    def __init__(self, init_match=None, init_field_wildcard=False):

        self.traffic = None

        self.switch_modifications = {}
        self.written_modifications = {}
        self.instruction_type = None

        self.match_fields = {}

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

    def get_field_intersection(self, tree1, tree2):

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
            intersection_element.match_fields[field_name] = self.get_field_intersection(
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

    # Computes A - B  = A Intersect B'
    # A is in_traffic_element
    # B here is self
    def get_diff_traffic_elements(self, in_traffic_element):

        # Work avoidance check: If there is no intersection between the two elemenet, don't bother with difference...
        if not in_traffic_element.intersect(self):
            return [in_traffic_element]

        # find B'
        complement_traffic_elements = self.get_complement_traffic_elements()

        # Do the intersection
        diff_traffic_elements = []
        for cme in complement_traffic_elements:
            i = in_traffic_element.intersect(cme)
            if i:
                diff_traffic_elements.append(i)

        return diff_traffic_elements

    # Checks if in_traffic_element is a subset of self
    # A is_subset of B if A - B == NullSet
    # A is in_traffic_element
    # B here is self
    def is_subset(self, in_traffic_element):

        diff_traffic_elements = self.get_diff_traffic_elements(in_traffic_element)

        # Return True/False based on if there was anything found in A Int B'
        if diff_traffic_elements:
            return False
        else:
            return True

    def get_modified_traffic_element(self):

        modified_traffic_element = TrafficElement()

        for field_name in self.match_fields:

            # TODO: If this fields needs to be modified, apply the modification
            if field_name in self.switch_modifications:
                modified_traffic_element.match_fields[field_name] = self.match_fields[field_name]

            else:
                # Otherwise, just keep the field same as it was
                modified_traffic_element.match_fields[field_name] = self.match_fields[field_name]

        return modified_traffic_element

    def get_orig_traffic_element(self, applied_modifications=None, store_switch_modifications=True):

        if applied_modifications:
            mf = applied_modifications
        else:
            # if the output_action type is applied, no written modifications take effect.
            if self.instruction_type == "applied":
                return self

            mf = self.written_modifications

        orig_traffic_element = TrafficElement()

        for field_name in field_names:

            # If the field is modified in the Traffic as it passes through a rule,
            # The original traffic that comes at the front of that rule is computed as follows:

            # If the field was not modified, then it is left as-is, no harm done
            # If the field is modified however, it is left as-is too, unless it is modified to the exact value
            # as it is contained in the traffic

            if field_name in mf:

                # Check to see if the value on this traffic is same as what it was modified to be for this modification
                # If it is, then use the 'original' value of the match that caused the modification. This is stored in mf
                # If it is not, then the assumption here would be that even though the modification is there on this chunk
                # but it does not really apply because of what the traffic chunk has gone through subsequently

                #TODO: Do this tree building thing more properly ground up from the parser
                field_val = int(mf[field_name][1])
                value_tree = IntervalTree()
                value_tree.add(Interval(field_val, field_val + 1))

                intersection = self.get_field_intersection(value_tree, self.match_fields[field_name])

                if intersection:
                    orig_traffic_element.match_fields[field_name] = mf[field_name][0].match_fields[field_name]
                else:
                    orig_traffic_element.match_fields[field_name] = self.match_fields[field_name]

            else:
                # Otherwise, just keep the field same as it was
                orig_traffic_element.match_fields[field_name] = self.match_fields[field_name]

        # Accumulate field modifications
        orig_traffic_element.written_modifications.update(self.written_modifications)
        orig_traffic_element.instruction_type = self.instruction_type

        if store_switch_modifications:
            orig_traffic_element.switch_modifications.update(mf)

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

    # Checks if in_te is subset of self (any one of its te)

    def is_subset_te(self, in_te):

        is_subset = False
        for self_te in self.traffic_elements:
            if self_te.is_subset(in_te):
                is_subset = True
                break

        return is_subset

    # Checks if in_traffic is a subset of self

    def is_subset_traffic(self, in_traffic):

        is_subset = True

        # Each one of the in_te has to be subset of self
        for in_te in in_traffic.traffic_elements:
            is_subset_te = self.is_subset_te(in_te)
            if not is_subset_te:
                is_subset = False
                break

        return is_subset

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

                    ei.written_modifications.update(e_in.written_modifications)
                    ei.instruction_type = e_in.instruction_type
                    ei.switch_modifications = e_in.switch_modifications

        return traffic_intersection

    # Computes a difference between two traffic instances and if they have changed.
    # Computes A - B, where A is in_traffic and B is self
    def difference(self, in_traffic):

        diff_traffic = Traffic()

        # If what is being subtracted is empty, then just return in_traffic
        if not self.traffic_elements:
            diff_traffic.traffic_elements.extend(in_traffic.traffic_elements)
            return diff_traffic

        #print "in_traffic.traffic_elements:", len(in_traffic.traffic_elements), "self.traffic_elements:", len(self.traffic_elements)

        for in_te in in_traffic.traffic_elements:

            remaining = [in_te]

            for self_te in self.traffic_elements:

                # This is the recursive case
                if len(remaining) > 1:
                    remaining_traffic = Traffic()
                    remaining_traffic.traffic_elements.extend(remaining)
                    to_subtract = Traffic()
                    to_subtract.traffic_elements.append(self_te)

                    remaining_traffic = to_subtract.difference(remaining_traffic)
                    remaining = remaining_traffic.traffic_elements

                # This is the base case
                elif len(remaining) == 1:
                    remaining = self_te.get_diff_traffic_elements(remaining[0])

                    if len(remaining) > 1:
                        pass

                else:
                    break

            # If there is anything that is left after all the differences have happened, then add it to diff_traffic
            if remaining:
                diff_traffic.traffic_elements.extend(remaining)

        return diff_traffic

    # Returns the new traffic that just got added
    def union(self, in_traffic):

        for union_te in in_traffic.traffic_elements:
            union_te.traffic = self
            self.traffic_elements.append(union_te)
        return self

    def get_orig_traffic(self, modifications=None, store_switch_modifications=True):

        orig_traffic = Traffic()
        for te in self.traffic_elements:
            orig_te = te.get_orig_traffic_element(modifications, store_switch_modifications)
            orig_te.traffic = orig_traffic
            orig_traffic.traffic_elements.append(orig_te)
        return orig_traffic

    def get_modified_traffic(self):

        modified_traffic = Traffic()

        for te in self.traffic_elements:
            modified_te = te.get_modified_traffic_element()
            modified_te.traffic = modified_traffic
            modified_traffic.traffic_elements.append(modified_te)
        return modified_traffic

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