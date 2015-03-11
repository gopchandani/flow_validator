__author__ = 'Rakesh Kumar'

from match import MatchElement
from copy import copy

class Traffic():

    def __init__(self, init_wildcard=False):

        self.match_elements = []

        # If initialized as wildcard, add one to the list
        if init_wildcard:
            self.match_elements.append(MatchElement(is_wildcard=True))

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


    def intersect(self, in_match):
        im = Traffic()
        for e1 in self.match_elements:
            for e2 in in_match.match_elements:
                ei = e1.intersect(e2)
                if ei:
                    ei.traffic = im
                    im.match_elements.append(ei)
        return im

    def pipe_welding(self, now_admitted_match):

        # The predecessor will be taken from self and those predecessor need to be told too
        # The successors will be taken by now_admitted_match

        new_m = Traffic()

        # Check if this existing_me can be taken even partially by any of the candidates
        # TODO: This does not handle left-over cases when parts of the existing_me are taken by multiple candidate_me

        for existing_me in self.match_elements:
            existing_me_welded = False
            for candidate_me in now_admitted_match.match_elements:
                new_me = existing_me.pipe_welding(candidate_me)
                if new_me:
                    new_me.traffic = new_m
                    new_m.match_elements.append(new_me)
                    existing_me_welded = True
                    break

            # If none of the candidate_me took existing_me:
            #Delete everybody who dependent on existing_me, the whole chain...
            if not existing_me_welded:
                existing_me.remove_with_predecessors()
        return new_m

    def union(self, in_match):

        for union_me in in_match.match_elements:
            union_me.traffic = self
            self.match_elements.append(union_me)

        return self

    def get_orig_match(self, modified_fields, matching_element):

        orig_match = Traffic()
        for me in self.match_elements:
            orig_me = me.get_orig_match_element(modified_fields, matching_element)
            orig_me.traffic = orig_match
            orig_match.match_elements.append(orig_me)
        return orig_match

    def get_orig_match_2(self):
        orig_match = Traffic()
        for me in self.match_elements:
            orig_me = me.get_orig_match_element()
            orig_me.traffic = orig_match
            orig_match.match_elements.append(orig_me)
        return orig_match

    def set_port(self, port):
        for me in self.match_elements:
            me.port = port

    def set_succ_match_element(self, succ_match_element):
        for me in self.match_elements:
            me.succ_match_element = succ_match_element
            succ_match_element.pred_match_elements.append(me)

    def set_edge_data_key(self, edge_data_key):
        for me in self.match_elements:
            me.edge_data_key = edge_data_key

    def accumulate_written_field_modifications(self, in_written_field_modifications, in_match_element):
        for me in self.match_elements:
            me.written_field_modifications.update(in_written_field_modifications)
            me.causing_match_element = in_match_element

    def is_field_wildcard(self, field_name):
        retval = True

        for me in self.match_elements:
            retval = me.is_field_wildcard(field_name)
            if not retval:
                break

        return retval

    def print_port_paths(self):

        for me in self.match_elements:
            port_path_str = me.port.port_id + "(" + str(id(me)) + ")"

            trav = me.succ_match_element

            while trav != None:

                port_path_str += (" -> " + trav.port.port_id + "(" + str(id(trav)) + ")")

                trav = trav.succ_match_element

            print port_path_str

def main():
    m1 = Traffic()
    print m1

    m2 = Traffic()
    m3 = m1.intersect(m2)
    print m3

if __name__ == "__main__":
    main()