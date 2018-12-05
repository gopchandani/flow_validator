import sys

from netaddr import IPNetwork
from match import field_names
from model.intervaltree_modified import IntervalTree, Interval


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

        if isinstance(field_val, Interval):
            return True
        else:
            return False

    def is_wildcard(self):
        is_wildcard = False

        for field_name in self.traffic_fields:
            field = self.traffic_fields[field_name]

            if self.is_traffic_field_wildcard(field):
                is_wildcard = True
            else:
                is_wildcard = False
                break

        return is_wildcard

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

            # Deal with IP Network fields
            if field_name == 'src_ip_addr' or field_name == 'dst_ip_addr':
                if isinstance(value, IPNetwork):
                    self.traffic_fields[field_name].chop(value.first, value.last + 1)
                else:
                    raise Exception("Gotta be IPNetwork!")
            else:
                self.traffic_fields[field_name].chop(value, value + 1)

    def get_field_intersection(self, field1, field2):

        # If either one of the fields is empty (i.e. no intervals), then there is no intersection to be had...
        if not self.is_traffic_field_wildcard(field1) and field1.is_empty():
            return None

        if not self.is_traffic_field_wildcard(field2) and field2.is_empty():
            return None

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

    def get_modified_traffic_element(self, use_embedded_switch_modifications):

        modified_traffic_element = TrafficElement()

        mf = None
        if use_embedded_switch_modifications:
            mf = self.switch_modifications
        else:
            if self.enabling_edge_data and self.enabling_edge_data.applied_modifications:
                mf = self.enabling_edge_data.applied_modifications
            else:
                mf = {}

        for field_name in self.traffic_fields:

            if field_name in mf:
                modified_traffic_element.traffic_fields[field_name] = mf[field_name][1]
            else:
                # Otherwise, just keep the field same as it was
                modified_traffic_element.traffic_fields[field_name] = self.traffic_fields[field_name].copy()

        # Accumulate field modifications
        modified_traffic_element.switch_modifications.update(self.switch_modifications)
        modified_traffic_element.written_modifications.update(self.written_modifications)
        modified_traffic_element.written_modifications_apply = self.written_modifications_apply
        modified_traffic_element.enabling_edge_data = self.enabling_edge_data

        return modified_traffic_element

    def get_orig_field(self, orig_traffic_element, field_name, modifications):

        # Check to see if the tree on this field has an intersection with value tree of what it is being modified to
        intersection = self.get_field_intersection(modifications[field_name][1], self.traffic_fields[field_name])

        # If it is, then use the 'original' traffic that caused the modification.
        if intersection:
            orig_traffic_element.traffic_fields[field_name] = modifications[field_name][0].traffic_fields[field_name]

        # If not, then  even though the modification is there on this chunk but it does not really apply
        else:
            orig_traffic_element.traffic_fields[field_name] = self.traffic_fields[field_name]

        return intersection

    def store_switch_modifications(self, modifications):
        remove_has_vlan_tag_modification = False

        # When storing modifications, store the first one applied in the switch, with the match from the last
        # matching rule
        for modified_field in modifications:

            # If the modification is to push a vlan tag, then in order for it to be recorded
            #
            # if modified_field == "has_vlan_tag":
            #     pass

            # If the modification on this field has not been seen before, simply store it.
            if modified_field not in self.switch_modifications:
                self.switch_modifications[modified_field] = modifications[modified_field]

            # Otherwise if you have seen this field being modified previously...
            else:
                # Check if the previous modification requires setting of the match to this modification
                # If so, then use the match from this modification
                this_modification_match = modifications[modified_field][0]
                this_modification_value_tree = modifications[modified_field][1]

                prev_modification_match = self.switch_modifications[modified_field][0]
                prev_modification_value_tree = self.switch_modifications[modified_field][1]
                prev_match_field_value_tree = prev_modification_match.traffic_fields[modified_field]

                intersection = self.get_field_intersection(this_modification_value_tree, prev_match_field_value_tree)

                if intersection:
                    self.switch_modifications[modified_field] = (this_modification_match, prev_modification_value_tree)
                # else:
                #     # Don't need to count adding of a vlan_id tag if the vlan tag already existed...
                #     if modified_field == "vlan_id":
                #         remove_has_vlan_tag_modification = True

        # # if the flag above was set true, then remove has_vlan_tag from the modifications
        # if remove_has_vlan_tag_modification and "has_vlan_tag" in self.modifications :
        #     del self.switch_modifications["has_vlan_tag"]

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
        orig_traffic_element.switch_modifications.update(self.switch_modifications)
        orig_traffic_element.written_modifications.update(self.written_modifications)
        orig_traffic_element.written_modifications_apply = self.written_modifications_apply
        orig_traffic_element.enabling_edge_data = self.enabling_edge_data

        orig_traffic_element.store_switch_modifications(modifications_used)

        return orig_traffic_element
