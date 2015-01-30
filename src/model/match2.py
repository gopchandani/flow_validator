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
            elements_sizes = []
            elements = []
            for i in xrange(0, len(size_list)):
                
                elements.append(self.lowDict[low][size_list[i]])
                elements_sizes.append(elements[i].size)

            self.lowDict[low] = [elements_sizes, elements]

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
    
            elements_sizes, elements = self.lowDict[low]

            for j in xrange(0, len(elements)):

                # mark that range begins at low
                #
                self.qMap[low][1].add(elements[j].tag)
                high = low + elements[j].size

                if not high in self.qMap:
                    self.qMap[high] = [set(), set(), set()]

                # mark that range ends at high
                #
                self.qMap[high][2].add(elements[j].tag)

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
        elements_sizes = bisect.bisect_left(self.qMapIdx, low)

        if elements_sizes == len(self.qMapIdx):
            return set()

        if elements_sizes == 0 and low < self.qMapIdx[ 0 ] and self.qMapIdx[0] <= high:
            adrs = self.qMapIdx[ elements_sizes ]
            active = self.qMap[ adrs ][0]

        elif len(self.qMapIdx) >1 and elements_sizes+1 < len(self.qMapIdx) and self.qMapIdx[elements_sizes+1] == low:
            elements_sizes = elements_sizes+1
            adrs = self.qMapIdx[ elements_sizes ]
            active = self.qMap[ adrs ][0]

         # value at elements_sizes is strictly larger than low and value at elements_sizes-1
         # is strictly lower
         #
        elif 0< elements_sizes:
            adrs = self.qMapIdx[ elements_sizes-1 ]
            active = self.qMap[ adrs ][0] - self.qMap[ adrs ][2]
            elements_sizes = elements_sizes-1

         # self.qMapIdx[elements_sizes] < low or possibly self.qMapIdx[elements_sizes] == low
        else:
            if self.qMapIdx[elements_sizes] == low:
                adrs = self.qMapIdx[ elements_sizes ]
                active = self.qMap[ adrs ][1]
            else:
                active = set()

        elements_sizes = elements_sizes+1
        while elements_sizes < len(self.qMapIdx) and self.qMapIdx[ elements_sizes ] <= high:
            adrs = self.qMapIdx[elements_sizes]
            active = active | self.qMap[adrs][0]
            elements_sizes = elements_sizes+1

        return active

    def getElementIdx(self,low,high):
        try:
           elements_sizes, size_list = self.lowDict[low]
        except:
           return None

        size = high-low
        j = bisect.bisect_left(elements_sizes, size)
       
        if j != len(elements_sizes) and elements_sizes[j] == size:
           return j
        else:
           return None
        
    def setId(self,low,high,tag):
        eIdx = self.getElementIdx(low,high)
        if eIdx is None:
           return False
        elements_sizes, elements = self.lowDict[low]
        elements[eIdx].tag = tag 
        return True

    def getId(self,low,high):
        eIdx = self.getElementIdx(low,high)
        if eIdx is None:
           return None
        elements_sizes, elements = self.lowDict[low]
        tag = elements[eIdx].tag
        return tag

def main():

    m = MatchField()
    
    m.addElement(0, 4, 1)
    m.addElement(4, 9, 2)

    print m.cover(1, 100)

if __name__ == "__main__":
    main()
