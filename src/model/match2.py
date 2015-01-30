__author__ = 'Rakesh Kumar'

import pdb
import bisect 
import warnings
from netaddr import *

class MatchFieldElement(object):

    def __init__(self, low, high, tag):
        self.low  = low
        self.size = high - low

        self.tag = tag
        self.qMap = {}
        self.qMap

class MatchField(object):

    def __init__(self):

        self.lowDict = {}
        self.ordered = False

    def addElement(self, low, high, tag):

        if not low in self.lowDict:
            self.lowDict[low] = {} 
        
        size = high - low
        if not size in self.lowDict[low]:
            e = MatchFieldElement(low, high, tag)
            self.lowDict[low][size] = e
        else:
            pass

    def orderElements(self):

        self.ordered = True
        for low in self.lowDict:

            # before this call, self.lowDict[low] would be a dictionary of sizes.
            # after this call it will be a 2-element list of lists

            size_list = sorted(self.lowDict[low].keys())
            ordered_match_field_elements_sizes = []
            ordered_match_field_elements = []
            for i in xrange(0, len(size_list)):
                
                ordered_match_field_elements.append(self.lowDict[low][size_list[i]])
                ordered_match_field_elements_sizes.append(ordered_match_field_elements[i].size)

            self.lowDict[low] = [ordered_match_field_elements_sizes, ordered_match_field_elements]

    # build data structure suitable for determining intersection of
    # IP addresses and IP ranges with members of this map
    #
    def buildQueryMap(self):

        if not self.ordered:
            self.orderElements()

        self.qMap = {}
        self.qMapIdx = []

        for low in self.lowDict:
            if not low in self.qMap:
                # record set of ranges that include low, that start at low, and that end at low
                #
                self.qMap[low] = [set(), set(), set()]
    
            idx, L = self.lowDict[low]
            for j in xrange(0, len(idx)):

                if not L[j].tag:
                    continue

                # mark that range begins at low
                #
                self.qMap[low][1].add(L[j].tag)
                high = low+idx[j]
                if not high in self.qMap:
                    self.qMap[high] = [set(), set(), set()]

                # mark that range ends at high
                #
                self.qMap[high][2].add(L[j].tag)

        active = set()
        priorEnd = set()

        self.qMapIdx = sorted(self.qMap.keys())
  
        for pos in self.qMapIdx:

            [on, start, end] = self.qMap[pos]
            # compute the set of address blocks that include IP address 'pos'
            #
            active = (active | start ) - priorEnd
            self.qMap[pos][0] = active
            priorEnd = end

    # return a set of address block ids that intersect the range from low to high
    #
    def cover(self, low, high):

        if 'qMapIdx' not in self.__dict__:
            self.buildQueryMap()

         # where do we start the scan?
         #
        idx = bisect.bisect_left(self.qMapIdx, low)

        if idx == len(self.qMapIdx):
            return set()

        if idx == 0 and low < self.qMapIdx[ 0 ] and self.qMapIdx[0] <= high:
            adrs = self.qMapIdx[ idx ]
            active = self.qMap[ adrs ][0]

        elif len(self.qMapIdx) >1 and idx+1 < len(self.qMapIdx) and self.qMapIdx[idx+1] == low:
            idx = idx+1
            adrs = self.qMapIdx[ idx ]
            active = self.qMap[ adrs ][0]

         # value at idx is strictly larger than low and value at idx-1
         # is strictly lower
         #
        elif 0< idx:
            adrs = self.qMapIdx[ idx-1 ]
            active = self.qMap[ adrs ][0] - self.qMap[ adrs ][2]
            idx = idx-1

         # self.qMapIdx[idx] < low or possibly self.qMapIdx[idx] == low
        else:
            if self.qMapIdx[idx] == low:
                adrs = self.qMapIdx[ idx ]
                active = self.qMap[ adrs ][1]
            else:
                active = set()


        idx = idx+1
        while idx < len(self.qMapIdx) and self.qMapIdx[ idx ] <= high:
            adrs = self.qMapIdx[idx]
            active = active | self.qMap[adrs][0]
            idx = idx+1

        return active

    def getElementIdx(self,low,high):
        try:
           idx, size_list = self.lowDict[low]
        except:
           return None

        size = high-low
        j = bisect.bisect_left(idx, size)
       
        if j != len(idx) and idx[j] == size:
           return j
        else:
           return None
        
    def setId(self,low,high,tag):
        eIdx = self.getElementIdx(low,high)
        if eIdx is None:
           return False
        idx, L = self.lowDict[low]
        L[eIdx].tag = tag 
        return True

    def getId(self,low,high):
        eIdx = self.getElementIdx(low,high)
        if eIdx is None:
           return None
        idx, L = self.lowDict[low]
        tag = L[eIdx].tag
        return tag

def main():

    m = MatchField()
    
    m.addElement(0, 4, 1)
    m.addElement(4, 9, 2)

    print m.cover(1, 100)

if __name__ == "__main__":
    main()
