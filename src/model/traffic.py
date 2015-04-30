__author__ = 'Rakesh Kumar'

from match_element import MatchElement
from copy import copy

class Traffic():

    def __init__(self, init_wildcard=False):

        self.match_elements = []

        # If initialized as wildcard, add one to the list
        if init_wildcard:
            self.match_elements.append(MatchElement(is_wildcard=True))

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

        new_m = Traffic()

        # Check if this existing_me can be taken even partially by any of the candidates
        # TODO: This does not handle left-over cases when parts of the existing_me are taken by multiple candidate_me

        #print "pipe_welding has:", len(self.match_elements), "existing match elements to take care of..."

        for existing_me in self.match_elements:
            existing_me_welded = False
            for candidate_me in now_admitted_match.match_elements:
                new_me = existing_me.pipe_welding(candidate_me)
                if new_me:
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