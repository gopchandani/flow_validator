__author__ = 'Rakesh Kumar'


# One of these per destination at a given port
#TODO: Could paths be Trees?

class FlowPathElement:

    def __init__(self, port_id, admitted_match, next_element):

        self.admitted_match = admitted_match
        self.next_element = next_element
        self.port_id = port_id

    def accumulate_admitted_match(self, match):
        self.admitted_match = self.admitted_match.union(match)

    def get_path_str(self):

        path_str = self.port_id
        next = self.next_element

        while next:
            path_str += " -> " + next.port_id
            next = next.next_element

        return path_str

