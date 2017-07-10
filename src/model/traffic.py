from match import field_names
from traffic_element import TrafficElement

__author__ = 'Rakesh Kumar'


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

    def is_wildcard(self):
        is_wildcard = False

        for te in self.traffic_elements:
            if te.is_wildcard():
                is_wildcard = True
            else:
                is_wildcard = False
                break

        return is_wildcard

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

    def __eq__(self, other):
        return self.is_equal_traffic(other)

    def equal_modifications(self, mods1, mods2):

        if mods1.keys() and mods2.keys():
            pass

        equal_mods = True

        # First check if the keys in the modification are not same
        if set(mods1.keys()) != set(mods2.keys()):
            equal_mods = False
        else:
            # then compare for each key, the modification applied is same
            for mf in mods1.keys():
                if mods1[mf] != mods2[mf]:
                    equal_mods = False
                    break

        return equal_mods

    def intersect(self, in_traffic, keep_all=False):
        traffic_intersection = Traffic()
        for e_in in in_traffic.traffic_elements:
            for e_self in self.traffic_elements:
                ei = e_self.intersect(e_in)
                if ei:

                    if not keep_all:

                        # Check to see if this intersection can be expressed as subset of any of the previous
                        # te's that are already collected
                        is_subset = traffic_intersection.is_subset_te(ei)

                        # If so, no need to add this one to the mix
                        if is_subset:
                            continue

                    # Add this and do the necessary book-keeping...
                    traffic_intersection.traffic_elements.append(ei)

                    ei.switch_modifications.update(e_in.switch_modifications)
                    ei.written_modifications.update(e_in.written_modifications)
                    ei.written_modifications_apply = e_in.written_modifications_apply
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
                    remaining_te.switch_modifications.update(in_te.switch_modifications)
                    remaining_te.written_modifications.update(in_te.written_modifications)
                    remaining_te.written_modifications_apply = in_te.written_modifications_apply
                    remaining_te.enabling_edge_data = in_te.enabling_edge_data

                diff_traffic.traffic_elements.extend(remaining)

        return diff_traffic

    # Returns the new traffic that just got added
    def union(self, in_traffic):
        self.traffic_elements.extend(in_traffic.traffic_elements)

    def get_orig_traffic(self,
                         provided_modifications=None,
                         use_embedded_written_modifications=False,
                         use_embedded_switch_modifications=False):

        orig_traffic = Traffic()
        for te in self.traffic_elements:

            modifications = None

            # If modifications are not provided, then fish for modifications embedded in the te
            if not provided_modifications:
                if use_embedded_written_modifications:
                    if not te.written_modifications_apply:
                        orig_traffic.traffic_elements.append(te)
                        continue
                    modifications = te.written_modifications
                elif use_embedded_switch_modifications:
                    modifications = te.switch_modifications
                else:
                    raise Exception("No modifications provided")
            else:
                modifications = provided_modifications

            # If the modifications are not empty
            if modifications:
                orig_te = te.get_orig_traffic_element(modifications)
            else:
                orig_te = te

            orig_traffic.traffic_elements.append(orig_te)

        return orig_traffic

    def get_modified_traffic(self, use_embedded_switch_modifications=False):

        modified_traffic = Traffic()

        for te in self.traffic_elements:
            modified_te = te.get_modified_traffic_element(use_embedded_switch_modifications)
            modified_traffic.traffic_elements.append(modified_te)
        return modified_traffic

    def set_enabling_edge_data(self, enabling_edge_data):
        for te in self.traffic_elements:
            te.enabling_edge_data = enabling_edge_data

    def set_written_modifications(self, written_modifications):
        for te in self.traffic_elements:
            te.written_modifications.update(written_modifications)
            te.store_switch_modifications(written_modifications)

    def set_written_modifications_apply(self, written_modifications_apply):
        for te in self.traffic_elements:
            te.written_modifications_apply = written_modifications_apply

    def get_enabling_edge_data(self):
        enabling_edge_data_list = []

        for te in self.traffic_elements:
            enabling_edge_data_list.append(te.enabling_edge_data)

        return enabling_edge_data_list
