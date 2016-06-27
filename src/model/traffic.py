import sys

from netaddr import IPNetwork
from match import field_names
from model import intervaltree_modified
from model.intervaltree_modified import IntervalTree, Interval

__author__ = 'Rakesh Kumar'


class TrafficElement:

    def __init__(self, init_match=None, init_field_wildcard=False):

        self.switch_modifications = {}
        self.written_modifications = {}
        self.written_modifications_apply = None
        self.traffic_fields = {}
        self.enabling_edge_data = None
        
        # If a match has been provided to initialize with
        if init_match:
            for field_name in field_names:
                if init_match.is_match_field_wildcard(field_name):
                    self.set_traffic_field(field_name, set_wildcard=True)
                else:
                    self.set_traffic_field(field_name, init_match[field_name])

        # Create one IntervalTree per field and put the wildcard interval in it
        elif init_field_wildcard:
            for field_name in field_names:
                self.set_traffic_field(field_name, set_wildcard=True)

    def __str__(self):

        te_str = ''
        for i in range(len(field_names) - 1):

            if not self.is_traffic_field_wildcard(self.traffic_fields[field_names[i]]):
                te_str += field_names[i] + ":" + str(self.traffic_fields[field_names[i]]) + "\r\n"
            else:
                pass

        te_str += field_names[len(field_names) - 1] + ":" + str(self.traffic_fields[field_names[len(field_names) - 1]])
        te_str += "\r\n"

        return te_str

    def is_traffic_field_wildcard(self, field_val):

        if isinstance(field_val, intervaltree_modified.Interval):
            return True
        else:
            return False

    def set_traffic_field(self, field_name, value=None, set_wildcard=False, is_exception_value=False):

        if set_wildcard:
            self.traffic_fields[field_name] = Interval(0, sys.maxsize)

        elif not is_exception_value:

            # If the field already exists in the Traffic Element, then clear it, otherwise spin up an IntervalTree
            if field_name not in self.traffic_fields:
                self.traffic_fields[field_name] = IntervalTree()
            else:

                if self.is_traffic_field_wildcard(self.traffic_fields[field_name]):
                    self.traffic_fields[field_name] = IntervalTree()
                else:
                    self.traffic_fields[field_name].clear()

            # Deal with IP Network fields
            if field_name == 'src_ip_addr' or field_name == 'dst_ip_addr':
                if isinstance(value, IPNetwork):
                    self.traffic_fields[field_name].add(Interval(value.first, value.last + 1))
                else:
                    raise Exception("Gotta be IPNetwork!")
            else:
                self.traffic_fields[field_name].add(Interval(value, value + 1))

        elif is_exception_value:

            if self.is_traffic_field_wildcard(self.traffic_fields[field_name]):
                self.traffic_fields[field_name] = IntervalTree()
            else:
                self.traffic_fields[field_name].clear()

            self.traffic_fields[field_name].add(Interval(0, sys.maxsize))
            self.traffic_fields[field_name].chop(value, value + 1)

    def get_field_intersection(self, field1, field2):

        # If either one of fields is a wildcard, other is the answer
        if self.is_traffic_field_wildcard(field1):
            return field2
        elif self.is_traffic_field_wildcard(field2):
            return field1
        else:
            # If neither is a wildcard, then we have to get down to brasstacks and do the intersection
            field_intersection_intervals = []

            for iv in field1:
                if type(iv) == int:
                    self.is_traffic_field_wildcard(field1)

                for matched_iv in field2.search(iv.begin, iv.end):

                    # Take the smaller interval of the two and put it in the field_intersection
                    if matched_iv.contains_interval(iv):
                        small_iv = Interval(iv.begin, iv.end)
                        field_intersection_intervals.append(small_iv)

                    elif iv.contains_interval(matched_iv):
                        small_iv = Interval(matched_iv.begin, matched_iv.end)
                        field_intersection_intervals.append(small_iv)

                    elif iv.overlaps(matched_iv.begin, matched_iv.end):
                        overlapping_interval = Interval(max(matched_iv.begin, iv.begin), min(matched_iv.end, iv.end))
                        field_intersection_intervals.append(overlapping_interval)

                    else:
                        raise Exception("Probably should never get here")

            if field_intersection_intervals:
                return IntervalTree(field_intersection_intervals)
            else:
                return None

    def intersect(self, in_traffic_element):

        intersection_element = TrafficElement()

        for field_name in field_names:
            intersection_element.traffic_fields[field_name] = self.get_field_intersection(
                in_traffic_element.traffic_fields[field_name], self.traffic_fields[field_name])

            # If the resulting tree has no intervals in it, then balk:
            if not intersection_element.traffic_fields[field_name]:
                return None

        return intersection_element

    def get_complement_traffic_elements(self):

        complement_traffic_elements = []
        for field_name in field_names:

            # If the field is not a wildcard, then chop it from the wildcard initialized Traffic
            if not self.is_traffic_field_wildcard(self.traffic_fields[field_name]):
                te = TrafficElement(init_field_wildcard=True)
                te.traffic_fields[field_name] = IntervalTree()
                te.traffic_fields[field_name].add(Interval(0, sys.maxsize))

                # Chop out each interval from te[field_name]
                for interval in self.traffic_fields[field_name]:
                    te.traffic_fields[field_name].chop(interval.begin, interval.end)

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

        for field_name in self.traffic_fields:

            if self.enabling_edge_data and self.enabling_edge_data.applied_modifications:
                if field_name in self.enabling_edge_data.applied_modifications:

                    field_interval = self.enabling_edge_data.applied_modifications[field_name][1]
                    value_tree = IntervalTree()
                    value_tree.add(field_interval)

                    modified_traffic_element.traffic_fields[field_name] = value_tree

                else:
                    # Otherwise, just keep the field same as it was
                    modified_traffic_element.traffic_fields[field_name] = self.traffic_fields[field_name]
            else:
                # Otherwise, just keep the field same as it was
                modified_traffic_element.traffic_fields[field_name] = self.traffic_fields[field_name]

        # Accumulate field modifications
        modified_traffic_element.written_modifications = self.written_modifications
        modified_traffic_element.switch_modifications = self.switch_modifications
        modified_traffic_element.written_modifications_apply = self.written_modifications_apply
        modified_traffic_element.enabling_edge_data = self.enabling_edge_data

        return modified_traffic_element

    def get_orig_field(self, orig_traffic_element, field_name, modifications):

        # Check to see if the value on this traffic is same as what it was modified to be for this modification
        # If it is, then use the 'original' value of the traffic that caused the modification.
        # If it is not, then the assumption here would be that even though the modification is there on this chunk
        # but it does not really apply because of what the traffic chunk has gone through subsequently

        field_interval = modifications[field_name][1]
        value_tree = IntervalTree()
        value_tree.add(field_interval)

        intersection = self.get_field_intersection(value_tree, self.traffic_fields[field_name])

        if intersection:
            orig_traffic_element.traffic_fields[field_name] = modifications[field_name][0].traffic_fields[field_name]
        else:
            orig_traffic_element.traffic_fields[field_name] = self.traffic_fields[field_name]

        return intersection

    def cascade_modifications(self, orig_traffic_element, modifications_used):

        # When storing modifications, store the first one applied in the switch, with the match from the last
        # matching rule
        for modified_field in modifications_used:
            if modified_field not in orig_traffic_element.switch_modifications:
                orig_traffic_element.switch_modifications[modified_field] = modifications_used[modified_field]
            else:
                # Check if the previous modification requires setting of the match to this modification
                # If so, then use the match from this modification
                this_modification_match = modifications_used[modified_field][0]
                this_modification_value_tree = modifications_used[modified_field][1]

                prev_modification_match = orig_traffic_element.switch_modifications[modified_field][0]
                prev_modification_value_tree = orig_traffic_element.switch_modifications[modified_field][1]

                prev_match_field_value_tree = prev_modification_match.traffic_fields[modified_field]

                intersection = self.get_field_intersection(this_modification_value_tree,
                                                           prev_match_field_value_tree)

                if intersection:
                    orig_traffic_element.switch_modifications[modified_field] = (this_modification_match,
                                                                                 prev_modification_value_tree)

        return orig_traffic_element

    def get_orig_traffic_element(self, modifications):

        modifications_used = {}
        modifications_used.update(modifications)

        orig_traffic_element = TrafficElement()

        for field_name in field_names:

            # If the field is modified in the Traffic as it passes through a rule,
            # The original traffic that comes at the front of that rule is computed as follows:

            # If the field was not modified, then it is left as-is, no harm done
            # If the field is modified however, it is left as-is too, unless it is modified to the exact value
            # as it is contained in the traffic

            if field_name in modifications:

                # Checking if the rule has both push_vlan and set_vlan modifications for the header,
                # if so, then don't sweat the push_vlan modification, the other one would take care of it, see below:
                if field_name == "has_vlan_tag" and "vlan_id" in modifications:
                    continue

                elif field_name == "vlan_id" and "has_vlan_tag" in modifications:
                    is_modified = self.get_orig_field(orig_traffic_element, field_name, modifications)
                    
                    if is_modified:
                        is_modified = self.get_orig_field(orig_traffic_element, "has_vlan_tag", modifications)
                    else:
                        # If ever reversing effects of push_vlan and not matching on it, while there is a modification
                        # on the has_vlan_tag as well then nullify this te. One way is to set has_vlan_tag to empty
                        empty_field = IntervalTree()
                        orig_traffic_element.traffic_fields["has_vlan_tag"] = empty_field

                elif field_name == "vlan_id" and "has_vlan_tag" not in modifications:

                    # Reverse the effects of a vlan_id modification on traffic only when a vlan tag is present
                    vlan_tag_present = False

                    # We check this by using a weird check here.
                    if self.is_traffic_field_wildcard(self.traffic_fields["has_vlan_tag"]):
                       vlan_tag_present = True
                    else:
                        if not Interval(0, 1) in self.traffic_fields["has_vlan_tag"]:
                            vlan_tag_present = True

                    if vlan_tag_present:
                        is_modified = self.get_orig_field(orig_traffic_element, field_name, modifications)
                    else:
                        orig_traffic_element.traffic_fields[field_name] = self.traffic_fields[field_name]
                        del modifications_used[field_name]

                # All the other fields...
                else:
                    is_modified = self.get_orig_field(orig_traffic_element, field_name, modifications)
            else:
                # Otherwise, just keep the field same as it was
                orig_traffic_element.traffic_fields[field_name] = self.traffic_fields[field_name]

        # Accumulate field modifications
        orig_traffic_element.written_modifications.update(self.written_modifications)
        orig_traffic_element.switch_modifications.update(self.switch_modifications)
        orig_traffic_element.written_modifications_apply = self.written_modifications_apply
        orig_traffic_element.enabling_edge_data = self.enabling_edge_data

        return self.cascade_modifications(orig_traffic_element, modifications_used)



class Traffic:

    def __init__(self, init_wildcard=False):

        self.traffic_elements = []

        # If initialized as wildcard, add one to the list
        if init_wildcard:
            self.traffic_elements.append(TrafficElement(init_field_wildcard=True))

    def __str__(self):
        t_str = ''

        for te in self.traffic_elements:
            t_str += "-----\r\n"
            t_str += str(te)

        t_str += "-----\r\n"
        return t_str

    def __del__(self):

        for te in self.traffic_elements:
            del te

    def add_traffic_elements(self, te_list):
        for te in te_list:
            self.traffic_elements.append(te)

    def is_empty(self):
        return len(self.traffic_elements) == 0

    def set_field(self, key, value=None, is_wildcard=False, is_exception_value=False):

        if key not in field_names:
            raise Exception('Invalid field name for set_field')

        if key and value and is_exception_value:
            for te in self.traffic_elements:
                te.set_traffic_field(key, value, is_exception_value=is_exception_value)

        elif key and is_wildcard:
            for te in self.traffic_elements:
                te.set_traffic_field(key, set_wildcard=True)

        else:
            for te in self.traffic_elements:
                te.set_traffic_field(key, value)

    def clear_switch_modifications(self):
        for te in self.traffic_elements:
            te.switch_modifications.clear()

    # Checks if in_te is subset of self (any one of its te)
    def is_subset_te(self, in_te):

        in_traffic = Traffic()
        in_traffic.traffic_elements.append(in_te)

        return self.is_subset_traffic(in_traffic)

    # Checks if in_traffic is a subset of self

    def is_subset_traffic(self, in_traffic):

        # First compute in_traffic - self
        diff_traffic = self.difference(in_traffic)

        # If difference is empty, then say that in_traffic is a subset of self
        if diff_traffic.is_empty():
            return True
        else:
            return False

    def is_equal_traffic(self, in_traffic):

        if self.is_subset_traffic(in_traffic) and in_traffic.is_subset_traffic(self):
            return True
        else:
            return False

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
                    traffic_intersection.traffic_elements.append(ei)

                    ei.written_modifications.update(e_in.written_modifications)
                    ei.written_modifications_apply = e_in.written_modifications_apply
                    ei.switch_modifications = e_in.switch_modifications
                    ei.enabling_edge_data = e_in.enabling_edge_data

        return traffic_intersection

    # Computes a difference between two traffic instances and if they have changed.
    # Computes A - B, where A is in_traffic and B is self
    def difference(self, in_traffic):

        diff_traffic = Traffic()

        # If what is being subtracted is empty, then just return in_traffic
        if not self.traffic_elements:
            diff_traffic.traffic_elements.extend(in_traffic.traffic_elements)
            return diff_traffic

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

                for remaining_te in remaining:
                    remaining_te.written_modifications = in_te.written_modifications
                    remaining_te.switch_modifications = in_te.switch_modifications
                    remaining_te.written_modifications_apply = in_te.written_modifications_apply
                    remaining_te.enabling_edge_data = in_te.enabling_edge_data

                diff_traffic.traffic_elements.extend(remaining)

        return diff_traffic

    # Returns the new traffic that just got added
    def union(self, in_traffic):
        self.traffic_elements.extend(in_traffic.traffic_elements)

    def get_orig_traffic(self, applied_modifications=None):

        orig_traffic = Traffic()
        for te in self.traffic_elements:

            if applied_modifications:
                modifications = applied_modifications
            else:
                if not te.written_modifications_apply:
                    orig_traffic.traffic_elements.append(te)
                    continue
                modifications = te.written_modifications

            if modifications:
                orig_te = te.get_orig_traffic_element(modifications)
            else:
                orig_te = te

            orig_traffic.traffic_elements.append(orig_te)

        return orig_traffic

    def get_intersecting_modifications(self):
        pass

    def get_modified_traffic(self):

        modified_traffic = Traffic()

        for te in self.traffic_elements:
            modified_te = te.get_modified_traffic_element()
            modified_traffic.traffic_elements.append(modified_te)
        return modified_traffic

    def set_enabling_edge_data(self, enabling_edge_data):
        for te in self.traffic_elements:
            te.enabling_edge_data = enabling_edge_data

    def set_written_modifications(self, written_modifications):
        for te in self.traffic_elements:
            te.written_modifications.update(written_modifications)

    def set_written_modifications_apply(self, written_modifications_apply):
        for te in self.traffic_elements:
            te.written_modifications_apply = written_modifications_apply

    def get_enabling_edge_data(self):
        enabling_edge_data_list = []

        for te in self.traffic_elements:
            enabling_edge_data_list.append(te.enabling_edge_data)

        return enabling_edge_data_list


def main():
    m1 = Traffic()
    print m1

    m2 = Traffic()
    m3 = m1.intersect(m2)
    print m3

if __name__ == "__main__":
    main()