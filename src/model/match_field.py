__author__ = 'Rakesh Kumar'

import sys
import bisect
from netaddr import *

class MatchFieldElement(object):

    def __init__(self, low, high, tag):
        self.low = low
        self.high = high
        self.size = high - low
        self.tag = tag

class MatchField(object):

    def __init__(self, field_name):

        self.field_name = field_name
        self.lowDict = {}
        self.ordered = False

    def add_element(self, low, high, tag):

        if not low in self.lowDict:
            self.lowDict[low] = {} 
        
        size = high - low
        if not size in self.lowDict[low]:
            e = MatchFieldElement(low, high, tag)
            self.lowDict[low][size] = e
        else:
            pass

    def order_elements(self):

        self.ordered = True
        for low in self.lowDict:

            # before: self.lowDict[low] would be a dictionary keyed by sizes containing MatchFieldElement objects
            # after: it will be a list of MatchFieldElement objects ordered by their size

            size_list = sorted(self.lowDict[low].keys())
            elements = []
            for i in xrange(0, len(size_list)):
                elements.append(self.lowDict[low][size_list[i]])

            self.lowDict[low] = elements


    # build data structure suitable for determining intersection of elements
    # This essentially takes form of a dictionary self.qMap, keyed by places of 'interest' (pos),
    # i.e. where elements begin and end, all of these keys are also maintained in a list self.boundaries
    # The dictionary self.qMap contains as values a list of three sets;

    # set of all tags of elements that 'occupy'/run through at that place of interest
    # set of all tags of elements that begin at that place of interest
    # set of all tags of elements that end at that place of interest

    def buildQueryMap(self):

        if not self.ordered:
            self.order_elements()

        self.qMap = {}
        self.boundaries = []

        for low in self.lowDict:
            if not low in self.qMap:

                # record set of ranges that include low, that start at low, and that end at low
                self.qMap[low] = [set(), set(), set()]

            elements = self.lowDict[low]
            for j in xrange(0, len(elements)):

                # mark that range begins at low
                self.qMap[low][1].add(elements[j].tag)
                high = low + elements[j].size

                if not high in self.qMap:
                    self.qMap[high] = [set(), set(), set()]

                # mark that range ends at high
                self.qMap[high][2].add(elements[j].tag)

        active_tags = set()
        previously_ended_tags = set()

        self.boundaries = sorted(self.qMap.keys())
        for pos in self.boundaries:

            [on, start, end] = self.qMap[pos]

            # compute the set of elements that include element 'pos'
            active_tags = (active_tags | start) - previously_ended_tags
            self.qMap[pos][0] = active_tags
            previously_ended_tags = end

    # Returns a set of tags that intersect between the in_match_field and self
    def intersect(self, in_match_field_element):

        intersecting_set = set()

        intersecting_set = self.cover(in_match_field_element.low,
                                        in_match_field_element.high)

        return intersecting_set

    def complement(self, in_match_field_element):


        complement = self.complement_cover(in_match_field_element.low,
                                           in_match_field_element.high)


    def complement_cover(self, low, high):
        complement = set()
        complement = self.cover(0, low-1) | self.cover(high+1, sys.maxsize)
        return complement

    # return a set of element tags that cover the range from low to high
    def cover(self, low, high):

        if 'boundaries' not in self.__dict__:
            self.buildQueryMap()

        # Where do we start the scan?
        # i will be the index for going through boundaries array of places of interest
        i = bisect.bisect_left(self.boundaries, low)

        # If the i falls to the right of all of the places of interest,,,
        if i == len(self.boundaries):
            return set()

        # If i falls to the left of all of the places of interest and...
        # The low and high are such that that will include the first boundaries, then, collect the first one...
        # This also means that low here is strictly less than self.boundaries[0]

        if i == 0 and low < self.boundaries[0] and self.boundaries[0] <= high:
            adrs = self.boundaries[i]
            active_tags = self.qMap[adrs][0]

        # Sort of special case when i > 0 and there is one more guy which is exactly equal to low but is next to i
        # This seems like it happens because of bisect_left
        # Collect things from this next guy

        elif i > 0 and len(self.boundaries) > 1 and i + 1 < len(self.boundaries) and self.boundaries[i + 1] == low:
            i += 1
            adrs = self.boundaries[i]
            active_tags = self.qMap[adrs][0]

        # value at i is strictly larger than low and value at i-1 is strictly lower, so grab things from i-1
        elif i > 0:
            adrs = self.boundaries[i - 1]
            active_tags = self.qMap[adrs][0] - self.qMap[adrs][2]
            i -= 1

        # self.boundaries[i] < low or possibly self.boundaries[i] == low
        else:
            if self.boundaries[i] == low:
                adrs = self.boundaries[i]
                active_tags = self.qMap[adrs][1]
            else:
                active_tags = set()

        # This is including the rest of them...
        i += 1
        while i < len(self.boundaries) and self.boundaries[i] <= high:
            adrs = self.boundaries[i]
            active_tags = active_tags | self.qMap[adrs][0]
            i += 1

        return active_tags


def main():

    m = MatchField("dummy")
    
    m.add_element(1, 2, "tag1")
    m.add_element(7, 9, "tag3")

    print m.cover(7, 10)

    #print m.complement_cover(4, 7)

if __name__ == "__main__":
    main()
