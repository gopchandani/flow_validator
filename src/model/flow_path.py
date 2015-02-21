__author__ = 'Rakesh Kumar'


# One of these per destination at a given port

class FlowPathElement:

    def __init__(self, admitted_match, relies_on):

        self.admitted_match = admitted_match
        self.relies_on = relies_on

    def accumulate_admitted_match(self, match):
        self.admitted_match = self.admitted_match.union(match)