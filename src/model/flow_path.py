__author__ = 'Rakesh Kumar'


# One of these per destination at a given port
#TODO: Could paths be Trees?

class FlowPathElement:

    def __init__(self, port_id, admitted_match, relies_on):

        self.admitted_match = admitted_match
        self.relies_on = relies_on
        self.port_id = port_id

    def accumulate_admitted_match(self, match):
        self.admitted_match = self.admitted_match.union(match)

    def get_path_str(self):

        path_str = self.port_id
        next = self.relies_on

        while next:
            path_str += " -> " + next.port_id
            next = next.relies_on

        return path_str

