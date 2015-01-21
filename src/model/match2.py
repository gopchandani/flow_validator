'''
Created on October 27, 2013

'''
# poke for good measure

from __future__ import print_function
import pdb
import bisect 
import warnings
from mynetaddr import *
from shared import *
from state.gateway import Gateway
from state.addressblock import AddressBlock
from analysis.analysis_utils import bsLeft

class AddressMapElement(object):
    def __init__(self, low, high, netId, rId=None):
        self.low  = low
        self.size = high - low
        self.rules = set()

        if rId:
           self.rules.add(rId)

        self.id = netId
        self.qMap = {}
        self.qMap

class AddressMap(object):

    def __init__(self, type):

        self.lowDict = {}

        # type is 'src' or 'dst'
        #
        self.type = type
        self.ordered = False

    def addElement(self, low, high, netId, rId):

         if not low in self.lowDict:
             self.lowDict[low] = {} 

         # store only unique sizes for each starting point
         #
         size = high - low

         if not size in self.lowDict[low]:
             e = AddressMapElement(low, high, netId, rId)
             self.lowDict[low][size] = e
         else:
             self.lowDict[low][size].rules.add(rId)
 
    def orderElements(self):

       self.ordered = True
       for low in self.lowDict:

          # before this call, self.size[s] will be a list.
          # after this call it will be a pair of lists
          #
          sList = sorted(self.lowDict[low].keys())

          # copy the low values into a key array we use for searching
          #
          idx = [0]*len(sList)
          L = [0]*len(sList)

          for i in xrange(0, len(sList)):
             L[i] = self.lowDict[low][sList[i]]
             idx[i] = L[i].size
         
          self.lowDict[low] = [idx, L]

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

              if not L[j].id:
                  continue

              ### DEC 4
              #if idx[j] == 4294967295:
              #    continue

              # mark that range begins at low
              # 
              self.qMap[low][1].add( L[j].id )    
              high = low+idx[j]
              if not high in self.qMap:
                 self.qMap[high] = [set(),set(),set()] 

              # mark that range ends at high
              #
              self.qMap[high][2].add( L[j].id )

       active = set()
       priorEnd = set()

       self.qMapIdx = sorted( self.qMap.keys() )
  
       for pos in self.qMapIdx: 

          [on,start,end] = self.qMap[pos]

          # compute the set of address blocks that include IP address 'pos'
          #
          active = (active | start ) - priorEnd
          self.qMap[pos][0] = active
          priorEnd = end 

    # return a set of address block ids that intersect the range from low to high
    #
    def cover(self,low,high):

         if 'qMapIdx' not in self.__dict__:
           self.buildQueryMap()

         # where do we start the scan?
         #
         idx = bisect.bisect_left( self.qMapIdx, low )
       
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
           idx, sList = self.lowDict[low]
        except:
           return None

        size = high-low
        j = bisect.bisect_left(idx, size)
       
        if j != len(idx) and idx[j] == size:
           return j
        else:
           return None
        
    def setId(self,low,high,id):
        eIdx = self.getElementIdx(low,high)
        if eIdx is None:
           return False
        idx, L = self.lowDict[low]
        L[eIdx].id = id 
        return True

    def getId(self,low,high):
        eIdx = self.getElementIdx(low,high)
        if eIdx is None:
           return None
        idx, L = self.lowDict[low]
        id = L[eIdx].id
        return id

    # return rules linked to the range described by low and high
    #
    def getRules(self,low,high):
        rset = set()
        coveringBlocks = self.cover(low,high)
        if coveringBlocks is None:
           return set()
        for abId in coveringBlocks:
           obj = shared.IdToObj[abId]
           idx, L = self.lowDict[obj.low]
           for e in L:
             if obj.high <= obj.low+e.size:
                 rset = rset | e.rules
        return rset 

    def makeRuleLinks(self):
       for low in self.lowDict:
         idx, L = self.lowDict[low]

         for e in L:

           #### DEC 4
           #if e.size == 4294967295:
           #  continue 
           eid = e.id 
           if eid is None:
              continue

           for r in e.rules:
             if self.type == 'src':
                shared.rule[ r ].srcABId.add( eid )
             else:
                shared.rule[ r ].dstABId.add( eid )
 
    # return list of 'related' networks
    #
    def getRelated(self,id):

         related = set() 
         if id not in shared.IdToObj:
            warnings.warn('run time error 13', stacklevel=2)
         ab   = shared.IdToObj[id]
         if not isinstance(ab,AddressBlock):
             return set()

         low  = ab.low
         high = ab.high

         present = True
         if self.getId(low,high) is None:
             present = False

         # make a list of the starting addresses, sorted
         #
         srtAdrs = sorted(self.lowDict.keys())
         i = 0

         # check for overlaps from the bottom
         #
         while i<len(srtAdrs) and srtAdrs[i] < low:
            try:
               idx, L = self.lowDict[ srtAdrs[i] ]
            except:
               warnings.warn('run time error 14', stacklevel=2)

            # necessary condition for any range that starts below
            # the target is that the largest block starting 
            # at srtAdrs[i] overlap the target.  If it does, then
            # march backward through sizes, including each containing block
            #
            if low <= srtAdrs[i]+idx[-1]:
                for j in reversed( xrange(0,len(idx)) ):

                   ## DEC 4
                   #if idx[j] == 4294967295:
                   #    continue
                   if low <= srtAdrs[i]+idx[j]:
                         if not L[j].id is None and not isinstance( shared.IdToObj[ L[j].id ], Gateway):
                           related.add( L[j].id ) 
                   else:
                     break
            i = i+1

         # necessary condition for range starting after low is that low overlaps it
         #
         while i< len(srtAdrs) and srtAdrs[i] <= high: 

            idx, L  = self.lowDict[ srtAdrs[i] ]
            for j in xrange(0,len(L)):
                if L[j].size < 4294967295:
                   if not L[j].id is None and not isinstance( shared.IdToObj[ L[j].id ], Gateway):
                     related.add( L[j].id )

            i = i+1

         # that's all!
         #
         return related

    def listOrphans(self):

       reported = {}

       # (a) --- has every rule range been mapped to a network object?

       # with country codes a zillion orphaned ranges might be thrown
       #
       # @return 3 lists with any networks, hosts or hosts found orphans
       #
       if not shared.lookupDict:

          for low in self.lowDict:
             sizes, L = self.lowDict[low]
             for i in xrange(0,len(sizes)):
               s = sizes[i] 
               e = L[i]

               # an Orphan might be reference to an interface IP, which is OK.
               # would be better to scan all the interfaces to double check
               #
               if e.id is None and s>0:
                     
                  high = low+s
                  ipr = IPRange(low,high)
                  print('WARNING: Orphaned range ',ipr,' referenced in rules ',e.rules, file=sys.stderr)
                  
       net_orphans = []
       hst_orphans = []
       rg_orphans  = []

       ab_pairs = ([shared.netlist,net_orphans],[shared.hostlist,hst_orphans],[shared.rangelist,rg_orphans])

       for sList, oList in ab_pairs:
           for abId in sList:
              ab = sList[abId]
              if ab.type == 'vlan':
                 continue
              if isinstance(ab,Gateway):
                   warnings.warn('run time error 15', stacklevel=2)

              low  = ab.low
              high = ab.high

              if self.getId(low,high) is None:

                  # get the relations and see if all of them are empty too
                  #
                  related = self.getRelated(abId)
                  found = False
                  for n in related:
                       net   = shared.IdToObj[n] 
                       if isinstance(net,Gateway):
                           continue
                       low  = net.low
                       high = net.high
                       if self.getId(low,high):
                           found = True
                           break 
                  if not found: 
                     oList.append(ab.name)
                     reported[ab.id] = True
                     #ab.reported = True
               
       return net_orphans, hst_orphans, rg_orphans, reported
