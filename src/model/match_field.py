__author__ = 'David M. Nicol'

import sys
import bisect
from netaddr import *
from copy import deepcopy

class MatchFieldElement(object):

    def __str__(self):
        if self._low == 0 and self._high == sys.maxsize:
            #return "|all|"
            return ""
        else:
            return "|low:" + str(self._low) + "|high:" + str(self._high) + "|"


    def __init__(self, low, high, tag):
        self._low = low
        self._high = high
        self._tag = tag
        self._size = high - low

    def is_wildcard(self):
        return self._low == 0 and self._high == sys.maxsize

    def complement_elements(self):
        complement_elements = []

        if 0 < self._low:
            complement_elements.append(MatchFieldElement(0, self._low - 1, "ce1"))

        if self._high < sys.maxsize:
            complement_elements.append(MatchFieldElement(self._high + 1, sys.maxsize, "ce2"))

        return complement_elements


class MatchField(object):

    def __init__(self, field_name):

        self.field_name = field_name
        self.pos_list = []
        self.pos_dict = {}
        self.element_dict = {}

    def __str__(self):

        if self.element_dict:
            ret_str = self.field_name + ": "
            field_elem = ""
            for e in self.element_dict:
                field_elem = field_elem + str(self.element_dict[e])

            if field_elem != "":
                ret_str = ret_str + field_elem
            else:
                ret_str = ""
        else:
            ret_str = self.field_name + ": Empty "

        return ret_str

    def remove_element_from_pos_dict(self, e):

        # If there is one element left and this is that one last element...
        if len(self.element_dict) == 1 and e._tag in self.element_dict:
            if e._low in self.pos_dict:
                del self.pos_dict[e._low]
                self.pos_list.remove(e._low)

            if e._high in self.pos_dict:
                del self.pos_dict[e._high]
                self.pos_list.remove(e._high)

            return

        # Check what previous ranges, this new range intersects with and update
        for prev_tag in self.cover(e._low, e._high):

            prev = self[prev_tag]

            # If I arrived on to myself, don't do anything...
            if prev._tag == e._tag:
                continue

            if e._low <= prev._low <= e._high and e._tag in self.pos_dict[e._low][0]:
                self.pos_dict[prev._low][0].remove(e._tag)

            if e._low <= prev._high <= e._high and e._tag in self.pos_dict[e._high][0]:
                self.pos_dict[prev._high][0].remove(e._tag)

        # Start with the low index
        if e._tag in self.pos_dict[e._low][0]:
            self.pos_dict[e._low][0].remove(e._tag)

        self.pos_dict[e._low][1].remove(e._tag)

        # Then the high index
        if e._tag in self.pos_dict[e._high][0]:
            self.pos_dict[e._high][0].remove(e._tag)

        self.pos_dict[e._high][2].remove(e._tag)

        # Check if nothing starts/stops at endpoints any more
        # if so, get rid of them from pos_dict and pos_list
        if not len(self.pos_dict[e._low][1]) and not len(self.pos_dict[e._low][2]):
            del self.pos_dict[e._low]
            self.pos_list.remove(e._low)

        if not len(self.pos_dict[e._high][1]) and not len(self.pos_dict[e._high][2]):
            del self.pos_dict[e._high]
            self.pos_list.remove(e._high)

    def add_element_to_pos_dict(self, e):

        def init_pos(pos):
            # If this new endpoint is new add it to appropriate place in pos_list and pos_dict
            if pos not in self.pos_dict:
                self.pos_dict[pos] = [set(), set(), set()]
                bisect.insort(self.pos_list, pos)

        init_pos(e._low)
        self.pos_dict[e._low][0].add(e._tag)
        self.pos_dict[e._low][1].add(e._tag)

        init_pos(e._high)
        self.pos_dict[e._high][0].add(e._tag)
        self.pos_dict[e._high][2].add(e._tag)

        # Check what previous ranges, this new range intersects with and update
        for prev_tag in self.cover(e._low, e._high):
            prev = self[prev_tag]

            # If I arrived on to myself
            if prev._tag == e._tag:
                continue

            if prev._low <= e._low <= prev._high:
                self.pos_dict[e._low][0].add(prev._tag)

            if prev._low <= e._high <= prev._high:
                self.pos_dict[e._high][0].add(prev._tag)

            if e._low <= prev._low <= e._high:
                self.pos_dict[prev._low][0].add(e._tag)

            if e._low <= prev._high <= e._high:
                self.pos_dict[prev._high][0].add(e._tag)

    def __delitem__(self, key):

        self.remove_element_from_pos_dict(self.element_dict[key])
        del self.element_dict[key]

    def keys(self):
        return self.element_dict.keys()

    def values(self):
        return self.element_dict.values()

    def __getitem__(self, item):
        return self.element_dict[item]

    def __setitem__(self, key, e):

        if e._tag != key:
            raise Exception("Invalid element being added tag != key")

        if key in self.element_dict:
            del self[key]
            self.element_dict[key] = e
            self.add_element_to_pos_dict(e)

        else:
            self.element_dict[key] = e
            self.add_element_to_pos_dict(e)

    # return a set of element tags that cover the range from low to high
    def cover(self, low, high):

        # If there are no elements to intersect this with...
        if not self.element_dict:
            return set()

        if 'pos_list' not in self.__dict__:
            self.buildQueryMap()

        # Where do we start the scan?
        # i will be the index for going through pos_list array of places of interest
        i = bisect.bisect_left(self.pos_list, low)

        # If the i falls to the right of all of the places of interest, then you are done, nothing intersects
        if i == len(self.pos_list):
            return set()

        # Case when the incoming range falls completely to the left of even the first one of pre-existing:
        # Collect the set of the first one
        if i == 0 and low < self.pos_list[0] and self.pos_list[0] <= high:
            pos = self.pos_list[i]
            active_tags = self.pos_dict[pos][0]

        # This seems like it happens because of bisect_left
        # Case when incoming range's low falls right on the pos immediately to the right of i:
        # Collect things from this pos on the right
        elif len(self.pos_list) > 1 and i + 1 < len(self.pos_list) and self.pos_list[i + 1] == low:
            i += 1
            pos = self.pos_list[i]
            active_tags = self.pos_dict[pos][0]


        # i falls in the middle of some things s.t. value at i is strictly larger than low
        # Collect things that are being carried forward from i-i
        elif i > 0:
            pos = self.pos_list[i - 1]
            active_tags = self.pos_dict[pos][0] - self.pos_dict[pos][2]
            i -= 1

        # i == 0 and (low > self.pos_list[0] or self.pos_list[0] == low):
        # Can this even happen?
        else:
            if low > self.pos_list[0]:
                raise Exception("This happened!")

            if self.pos_list[i] == low:
                pos = self.pos_list[i]
                active_tags = self.pos_dict[pos][1]
            else:
                active_tags = set()


        # Collect elements by sweeping right until you hit _high_
        i += 1
        while i < len(self.pos_list) and self.pos_list[i] <= high:
            pos = self.pos_list[i]
            active_tags = active_tags | self.pos_dict[pos][0]
            i += 1

        return active_tags

    #TODO: Need to figure out a way to determine if a particular tag was _fully_ in the intersection
    #TODO: Think 1---5 has 2-3 but not 4--6
    #TODO: This guy is not paying attention to exact ranges of intersection at all


    # Start with nothing and add things that have intersection
    def intersect(self, input_object):

        intersect_field = MatchField(self.field_name)
        in_match_field_elements = []

        if isinstance(input_object, MatchField):
            in_match_field_elements = input_object.values()

        elif isinstance(input_object, MatchFieldElement):
            in_match_field_elements = [input_object]

        for e in in_match_field_elements:

            cover_result = self.cover(e._low, e._high)

            # If the e is a wildcard, then add all of elements that this field has to the intersection
            if e.is_wildcard():
                for tag in cover_result:
                    intersect_field[tag] = self[tag]

            # If the e is not a wildcard, add only this one element IFF the cover exists
            else:
                if cover_result:
                    intersect_field[e._tag] = e

        return intersect_field


def main():

    m = MatchField("dummy")

    m["tag1"] = MatchFieldElement(1, 3, "tag1")
    m["tag2"] = MatchFieldElement(1, 4, "tag2")
    m["tag3"] = MatchFieldElement(7, 9, "tag3")
    m["tag4"] = MatchFieldElement(0, 5, "tag4")
    m["tag5"] = MatchFieldElement(5, sys.maxsize, "tag5")
    m["tag6"] = MatchFieldElement(0, sys.maxsize, "tag6")

    print m.cover(2, 10)
    print m.complement_cover(1, 2)

    a = m["tag1"].complement_elements()
    a = m["tag4"].complement_elements()
    a = m["tag5"].complement_elements()
    a = m["tag6"].complement_elements()


    print a

if __name__ == "__main__":
    main()
