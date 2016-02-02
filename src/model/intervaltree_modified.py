
import collections

from sortedcontainers import SortedDict
from warnings import warn
from numbers import Number
from collections import namedtuple

from operator import attrgetter
from math import floor, log


class Node(object):
    def __init__(self,
                 x_center=None,
                 s_center=set(),
                 left_node=None,
                 right_node=None):
        self.x_center = x_center
        self.s_center = set(s_center)
        self.left_node = left_node
        self.right_node = right_node
        self.depth = 0    # will be set when rotated
        self.balance = 0  # ditto
        self.rotate()

    @classmethod
    def from_interval(cls, interval):
        """
        :rtype : Node
        """
        center = interval.begin
        return Node(center, [interval])

    @classmethod
    def from_intervals(cls, intervals):
        """
        :rtype : Node
        """
        if not intervals:
            return None
        node = Node()
        node = node.init_from_sorted(sorted(intervals))
        return node

    def init_from_sorted(self, intervals):
        if not intervals:
            return None
        center_iv = intervals[len(intervals) // 2]
        self.x_center = center_iv.begin
        self.s_center = set()
        s_left = []
        s_right = []
        for k in intervals:
            if k.end <= self.x_center:
                s_left.append(k)
            elif k.begin > self.x_center:
                s_right.append(k)
            else:
                self.s_center.add(k)
        self.left_node = Node.from_intervals(s_left)
        self.right_node = Node.from_intervals(s_right)
        return self.rotate()

    def center_hit(self, interval):
        """Returns whether interval overlaps self.x_center."""
        return interval.contains_point(self.x_center)

    def hit_branch(self, interval):
        """
        Assuming not center_hit(interval), return which branch
        (left=0, right=1) interval is in.
        """
        return interval.begin > self.x_center

    def refresh_balance(self):
        """
        Recalculate self.balance and self.depth based on child node values.
        """
        left_depth = self.left_node.depth if self.left_node else 0
        right_depth = self.right_node.depth if self.right_node else 0
        self.depth = 1 + max(left_depth, right_depth)
        self.balance = right_depth - left_depth

    def compute_depth(self):
        """
        Recursively computes true depth of the subtree. Should only
        be needed for debugging. Unless something is wrong, the
        depth field should reflect the correct depth of the subtree.
        """
        left_depth = self.left_node.compute_depth() if self.left_node else 0
        right_depth = self.right_node.compute_depth() if self.right_node else 0
        return 1 + max(left_depth, right_depth)

    def rotate(self):
        """
        Does rotating, if necessary, to balance this node, and
        returns the new top node.
        """
        self.refresh_balance()
        if abs(self.balance) < 2:
            return self
        # balance > 0  is the heavy side
        my_heavy = self.balance > 0
        child_heavy = self[my_heavy].balance > 0
        if my_heavy == child_heavy or self[my_heavy].balance == 0:
            ## Heavy sides same
            #    self     save
            #  save   -> 1   self
            # 1
            #
            ## Heavy side balanced
            #    self     save         save
            #  save   -> 1   self  -> 1  self.rot()
            #  1  2         2
            return self.srotate()
        else:
            return self.drotate()

    def srotate(self):
        """Single rotation. Assumes that balance is +-2."""
        #     self        save         save
        #   save 3  ->   1   self  -> 1   self.rot()
        #  1   2            2   3
        #
        #  self            save                save
        # 3   save  ->  self  1    -> self.rot()   1
        #    2   1     3   2

        #assert(self.balance != 0)
        heavy = self.balance > 0
        light = not heavy
        save = self[heavy]
        #print("srotate: bal={},{}".format(self.balance, save.balance))
        #self.print_structure()
        self[heavy] = save[light]   # 2
        #assert(save[light])
        save[light] = self.rotate()  # Needed to ensure the 2 and 3 are balanced under new subnode

        # Some intervals may overlap both self.x_center and save.x_center
        # Promote those to the new tip of the tree
        promotees = [iv for iv in save[light].s_center if save.center_hit(iv)]
        if promotees:
            for iv in promotees:
                save[light] = save[light].remove(iv)  # may trigger pruning
            # TODO: Use Node.add() here, to simplify future balancing improvements.
            # For now, this is the same as augmenting save.s_center, but that may
            # change.
            save.s_center.update(promotees)
        save.refresh_balance()
        return save

    def drotate(self):
        # First rotation
        my_heavy = self.balance > 0
        self[my_heavy] = self[my_heavy].srotate()
        self.refresh_balance()

        # Second rotation
        result = self.srotate()

        return result

    def add(self, interval):
        """
        Returns self after adding the interval and balancing.
        """
        if self.center_hit(interval):
            self.s_center.add(interval)
            return self
        else:
            direction = self.hit_branch(interval)
            if not self[direction]:
                self[direction] = Node.from_interval(interval)
                self.refresh_balance()
                return self
            else:
                self[direction] = self[direction].add(interval)
                return self.rotate()

    def remove(self, interval):
        """
        Returns self after removing the interval and balancing.

        If interval is not present, raise ValueError.
        """
        # since this is a list, called methods can set this to [1],
        # making it true
        done = []
        return self.remove_interval_helper(interval, done, should_raise_error=True)

    def discard(self, interval):
        """
        Returns self after removing interval and balancing.

        If interval is not present, do nothing.
        """
        done = []
        return self.remove_interval_helper(interval, done, should_raise_error=False)

    def remove_interval_helper(self, interval, done, should_raise_error):
        """
        Returns self after removing interval and balancing.
        If interval doesn't exist, raise ValueError.

        This method may set done to [1] to tell all callers that
        rebalancing has completed.

        See Eternally Confuzzled's jsw_remove_r function (lines 1-32)
        in his AVL tree article for reference.
        """
        #trace = interval.begin == 347 and interval.end == 353
        #if trace: print('\nRemoving from {} interval {}'.format(
        #   self.x_center, interval))
        if self.center_hit(interval):
            #if trace: print('Hit at {}'.format(self.x_center))
            if not should_raise_error and interval not in self.s_center:
                done.append(1)
                #if trace: print('Doing nothing.')
                return self
            try:
                # raises error if interval not present - this is
                # desired.
                self.s_center.remove(interval)
            except:
                self.print_structure()
                raise KeyError(interval)
            if self.s_center:     # keep this node
                done.append(1)    # no rebalancing necessary
                #if trace: print('Removed, no rebalancing.')
                return self

            # If we reach here, no intervals are left in self.s_center.
            # So, prune self.
            return self.prune()
        else:  # interval not in s_center
            direction = self.hit_branch(interval)

            if not self[direction]:
                if should_raise_error:
                    raise ValueError
                done.append(1)
                return self

            #if trace:
            #   print('Descending to {} branch'.format(
            #       ['left', 'right'][direction]
            #       ))
            self[direction] = self[direction].remove_interval_helper(interval, done, should_raise_error)

            # Clean up
            if not done:
                #if trace:
                #    print('Rotating {}'.format(self.x_center))
                #    self.print_structure()
                return self.rotate()
            return self

    def search_overlap(self, point_list):
        """
        Returns all intervals that overlap the point_list.
        """
        result = set()
        for j in point_list:
            self.search_point(j, result)
        return result

    def search_point(self, point, result):
        """
        Returns all intervals that contain point.
        """
        for k in self.s_center:
            if k.begin <= point < k.end:
                result.add(k)
        if point < self.x_center and self[0]:
            return self[0].search_point(point, result)
        elif point > self.x_center and self[1]:
            return self[1].search_point(point, result)
        return result

    def prune(self):
        """
        On a subtree where the root node's s_center is empty,
        return a new subtree with no empty s_centers.
        """
        if not self[0] or not self[1]:    # if I have an empty branch
            direction = not self[0]       # graft the other branch here
            #if trace:
            #    print('Grafting {} branch'.format(
            #       'right' if direction else 'left'))

            result = self[direction]
            #if result: result.verify()
            return result
        else:
            # Replace the root node with the greatest predecessor.
            heir, self[0] = self[0].pop_greatest_child()
            #if trace:
            #    print('Replacing {} with {}.'.format(
            #        self.x_center, heir.x_center
            #        ))
            #    print('Removed greatest predecessor:')
            #    self.print_structure()

            #if self[0]: self[0].verify()
            #if self[1]: self[1].verify()

            # Set up the heir as the new root node
            (heir[0], heir[1]) = (self[0], self[1])
            #if trace: print('Setting up the heir:')
            #if trace: heir.print_structure()

            # popping the predecessor may have unbalanced this node;
            # fix it
            heir.refresh_balance()
            heir = heir.rotate()
            #heir.verify()
            #if trace: print('Rotated the heir:')
            #if trace: heir.print_structure()
            return heir

    def pop_greatest_child(self):
        """
        Used when pruning a node with both a left and a right branch.
        Returns (greatest_child, node), where:
          * greatest_child is a new node to replace the removed node.
          * node is the subtree after:
              - removing the greatest child
              - balancing
              - moving overlapping nodes into greatest_child

        Assumes that self.s_center is not empty.

        See Eternally Confuzzled's jsw_remove_r function (lines 34-54)
        in his AVL tree article for reference.
        """
        #print('Popping from {}'.format(self.x_center))
        if not self.right_node:         # This node is the greatest child.
            # To reduce the chances of an overlap with a parent, return
            # a child node containing the smallest possible number of
            # intervals, as close as possible to the maximum bound.
            ivs = sorted(self.s_center, key=attrgetter('end', 'begin'))
            max_iv = ivs.pop()
            new_x_center = self.x_center
            while ivs:
                next_max_iv = ivs.pop()
                if next_max_iv.end == max_iv.end: continue
                new_x_center = max(new_x_center, next_max_iv.end)
            def get_new_s_center():
                for iv in self.s_center:
                    if iv.contains_point(new_x_center): yield iv

            # Create a new node with the largest x_center possible.
            child = Node.from_intervals(get_new_s_center())
            #     [iv for iv in self.s_center if iv.contains_point(child_x_center)]
            # )
            child.x_center = new_x_center
            self.s_center -= child.s_center

            #print('Pop hit! Returning child   = {}'.format(
            #    child.print_structure(tostring=True)
            #    ))
            #assert not child[0]
            #assert not child[1]

            if self.s_center:
                #print('     and returning newnode = {}'.format( self ))
                #self.verify()
                return child, self
            else:
                #print('     and returning newnode = {}'.format( self[0] ))
                #if self[0]: self[0].verify()
                return child, self[0]  # Rotate left child up

        else:
            #print('Pop descent to {}'.format(self[1].x_center))
            (greatest_child, self[1]) = self[1].pop_greatest_child()
            self.refresh_balance()
            new_self = self.rotate()

            # Move any overlaps into greatest_child
            for iv in set(new_self.s_center):
                if iv.contains_point(greatest_child.x_center):
                    new_self.s_center.remove(iv)
                    greatest_child.add(iv)

            #print('Pop Returning child   = {}'.format(
            #    greatest_child.print_structure(tostring=True)
            #    ))
            if new_self.s_center:
                #print('and returning newnode = {}'.format(
                #    new_self.print_structure(tostring=True)
                #    ))
                #new_self.verify()
                return greatest_child, new_self
            else:
                new_self = new_self.prune()
                #print('and returning prune = {}'.format(
                #    new_self.print_structure(tostring=True)
                #    ))
                #if new_self: new_self.verify()
                return greatest_child, new_self

    def contains_point(self, p):
        """
        Returns whether this node or a child overlaps p.
        """
        for iv in self.s_center:
            if iv.contains_point(p):
                return True
        branch = self[p > self.x_center]
        return branch and branch.contains_point(p)

    def all_children(self):
        return self.all_children_helper(set())

    def all_children_helper(self, result):
        result.update(self.s_center)
        if self[0]:
            self[0].all_children_helper(result)
        if self[1]:
            self[1].all_children_helper(result)
        return result

    def verify(self, parents=set()):
        """
        ## DEBUG ONLY ##
        Recursively ensures that the invariants of an interval subtree
        hold.
        """
        assert(isinstance(self.s_center, set))

        bal = self.balance
        assert abs(bal) < 2, \
            "Error: Rotation should have happened, but didn't! \n{}".format(
                self.print_structure(tostring=True)
            )
        self.refresh_balance()
        assert bal == self.balance, \
            "Error: self.balance not set correctly! \n{}".format(
                self.print_structure(tostring=True)
            )

        assert self.s_center, \
            "Error: s_center is empty! \n{}".format(
                self.print_structure(tostring=True)
            )
        for iv in self.s_center:
            assert hasattr(iv, 'begin')
            assert hasattr(iv, 'end')
            assert iv.begin < iv.end
            assert iv.overlaps(self.x_center)
            for parent in sorted(parents):
                assert not iv.contains_point(parent), \
                    "Error: Overlaps ancestor ({})! \n{}\n\n{}".format(
                        parent, iv, self.print_structure(tostring=True)
                    )
        if self[0]:
            assert self[0].x_center < self.x_center, \
                "Error: Out-of-order left child! {}".format(self.x_center)
            self[0].verify(parents.union([self.x_center]))
        if self[1]:
            assert self[1].x_center > self.x_center, \
                "Error: Out-of-order right child! {}".format(self.x_center)
            self[1].verify(parents.union([self.x_center]))

    def __getitem__(self, index):
        """
        Returns the left child if input is equivalent to False, or
        the right side otherwise.
        """
        if index:
            return self.right_node
        else:
            return self.left_node

    def __setitem__(self, key, value):
        """Sets the left (0) or right (1) child."""
        if key:
            self.right_node = value
        else:
            self.left_node = value

    def __str__(self):
        """
        Shows info about this node.

        Since Nodes are internal data structures not revealed to the
        user, I'm not bothering to make this copy-paste-executable as a
        constructor.
        """
        return "Node<{0}, depth={1}, balance={2}>".format(
            self.x_center,
            self.depth,
            self.balance
        )
        #fieldcount = 'c_count,has_l,has_r = <{}, {}, {}>'.format(
        #    len(self.s_center),
        #    bool(self.left_node),
        #    bool(self.right_node)
        #)
        #fields = [self.x_center, self.balance, fieldcount]
        #return "Node({}, b={}, {})".format(*fields)

    def count_nodes(self):
        """
        Count the number of Nodes in this subtree.
        :rtype: int
        """
        count = 1
        if self.left_node:
            count += self.left_node.count_nodes()
        if self.right_node:
            count += self.right_node.count_nodes()
        return count

    def depth_score(self, n, m):
        """
        Calculates flaws in balancing the tree.
        :param n: size of tree
        :param m: number of Nodes in tree
        :rtype: real
        """
        if n == 0:
            return 0.0

        # dopt is the optimal maximum depth of the tree
        dopt = 1 + int(floor(log(m, 2)))
        f = 1 / float(1 + n - dopt)
        return f * self.depth_score_helper(1, dopt)

    def depth_score_helper(self, d, dopt):
        """
        Gets a weighted count of the number of Intervals deeper than dopt.
        :param d: current depth, starting from 0
        :param dopt: optimal maximum depth of a leaf Node
        :rtype: real
        """
        # di is how may levels deeper than optimal d is
        di = d - dopt
        if di > 0:
            count = di * len(self.s_center)
        else:
            count = 0
        if self.right_node:
            count += self.right_node.depth_score_helper(d + 1, dopt)
        if self.left_node:
            count += self.left_node.depth_score_helper(d + 1, dopt)
        return count

    def print_structure(self, indent=0, tostring=False):
        """
        For debugging.
        """
        nl = '\n'
        sp = indent * '    '

        rlist = [str(self) + nl]
        if self.s_center:
            for iv in sorted(self.s_center):
                rlist.append(sp + ' ' + repr(iv) + nl)
        if self.left_node:
            rlist.append(sp + '<:  ')  # no CR
            rlist.append(self.left_node.print_structure(indent + 1, True))
        if self.right_node:
            rlist.append(sp + '>:  ')  # no CR
            rlist.append(self.right_node.print_structure(indent + 1, True))
        result = ''.join(rlist)
        if tostring:
            return result
        else:
            print(result)

class Interval(namedtuple('IntervalBase', ['begin', 'end', 'data'])):
    __slots__ = ()  # Saves memory, avoiding the need to create __dict__ for each interval

    def __new__(cls, begin, end, data=None):
        return super(Interval, cls).__new__(cls, begin, end, data)

    def overlaps(self, begin, end=None):
        """
        Whether the interval overlaps the given point, range or Interval.
        :param begin: beginning point of the range, or the point, or an Interval
        :param end: end point of the range. Optional if not testing ranges.
        :return: True or False
        :rtype: bool
        """
        if end is not None:
            return (
                (begin <= self.begin < end) or
                (begin < self.end <= end) or
                (self.begin <= begin < self.end) or
                (self.begin < end <= self.end)
            )
        try:
            return self.overlaps(begin.begin, begin.end)
        except:
            return self.contains_point(begin)

    def contains_point(self, p):
        """
        Whether the Interval contains p.
        :param p: a point
        :return: True or False
        :rtype: bool
        """
        return self.begin <= p < self.end

    def contains_interval(self, other):
        """
        Whether other is contained in this Interval.
        :param other: Interval
        :return: True or False
        :rtype: bool
        """
        return (
            self.begin <= other.begin and
            self.end >= other.end
        )

    def is_null(self):
        """
        Whether this equals the null interval.
        :return: True if end <= begin else False
        :rtype: bool
        """
        return self.begin >= self.end

    def length(self):
        """
        The distance covered by this Interval.
        :return: length
        :type: Number
        """
        if self.is_null():
            return 0
        return self.end - self.begin

    def __hash__(self):
        """
        Depends on begin and end only.
        :return: hash
        :rtype: Number
        """
        return hash((self.begin, self.end))

    def __eq__(self, other):
        """
        Whether the begins equal, the ends equal, and the data fields
        equal. Compare range_matches().
        :param other: Interval
        :return: True or False
        :rtype: bool
        """
        return (
            self.begin == other.begin and
            self.end == other.end and
            self.data == other.data
        )

    def __cmp__(self, other):
        """
        Tells whether other sorts before, after or equal to this
        Interval.

        Sorting is by begins, then by ends, then by data fields.

        If data fields are not both sortable types, data fields are
        compared alphabetically by type name.
        :param other: Interval
        :return: -1, 0, 1
        :rtype: int
        """
        s = self[0:2]
        try:
            o = other[0:2]
        except:
            o = (other,)
        if s != o:
            return -1 if s < o else 1
        try:
            if self.data == other.data:
                return 0
            return -1 if self.data < other.data else 1
        except TypeError:
            s = type(self.data).__name__
            o = type(other.data).__name__
            if s == o:
                return 0
            return -1 if s < o else 1

    def __lt__(self, other):
        """
        Less than operator. Parrots __cmp__()
        :param other: Interval or point
        :return: True or False
        :rtype: bool
        """
        return self.__cmp__(other) < 0

    def __gt__(self, other):
        """
        Greater than operator. Parrots __cmp__()
        :param other: Interval or point
        :return: True or False
        :rtype: bool
        """
        return self.__cmp__(other) > 0

    def _raise_if_null(self, other):
        """
        :raises ValueError: if either self or other is a null Interval
        """
        if self.is_null():
            raise ValueError("Cannot compare null Intervals!")
        if hasattr(other, 'is_null') and other.is_null():
            raise ValueError("Cannot compare null Intervals!")

    def lt(self, other):
        """
        Strictly less than. Returns True if no part of this Interval
        extends higher than or into other.
        :raises ValueError: if either self or other is a null Interval
        :param other: Interval or point
        :return: True or False
        :rtype: bool
        """
        self._raise_if_null(other)
        return self.end <= getattr(other, 'begin', other)

    def le(self, other):
        """
        Less than or overlaps. Returns True if no part of this Interval
        extends higher than other.
        :raises ValueError: if either self or other is a null Interval
        :param other: Interval or point
        :return: True or False
        :rtype: bool
        """
        self._raise_if_null(other)
        return self.end <= getattr(other, 'end', other)

    def gt(self, other):
        """
        Strictly greater than. Returns True if no part of this Interval
        extends lower than or into other.
        :raises ValueError: if either self or other is a null Interval
        :param other: Interval or point
        :return: True or False
        :rtype: bool
        """
        self._raise_if_null(other)
        if hasattr(other, 'end'):
            return self.begin >= other.end
        else:
            return self.begin > other

    def ge(self, other):
        """
        Greater than or overlaps. Returns True if no part of this Interval
        extends lower than other.
        :raises ValueError: if either self or other is a null Interval
        :param other: Interval or point
        :return: True or False
        :rtype: bool
        """
        self._raise_if_null(other)
        return self.begin >= getattr(other, 'begin', other)

    def _get_fields(self):
        """
        Used by str, unicode, repr and __reduce__.

        Returns only the fields necessary to reconstruct the Interval.
        :return: reconstruction info
        :rtype: tuple
        """
        if self.data is not None:
            return self.begin, self.end, self.data
        else:
            return self.begin, self.end

    def __repr__(self):
        """
        Executable string representation of this Interval.
        :return: string representation
        :rtype: str
        """
        if isinstance(self.begin, Number):
            s_begin = str(self.begin)
            s_end = str(self.end)
        else:
            s_begin = repr(self.begin)
            s_end = repr(self.end)
        if self.data is None:
            return "Interval({0}, {1})".format(s_begin, s_end)
        else:
            return "Interval({0}, {1}, {2})".format(s_begin, s_end, repr(self.data))

    __str__ = __repr__

    def copy(self):
        """
        Shallow copy.
        :return: copy of self
        :rtype: Interval
        """
        return Interval(self.begin, self.end, self.data)

    def __reduce__(self):
        """
        For pickle-ing.
        :return: pickle data
        :rtype: tuple
        """
        return Interval, self._get_fields()


class IntervalTree(collections.MutableSet):

    def __init__(self, intervals=None):
        """
        Set up a tree. If intervals is provided, add all the intervals 
        to the tree.
        
        Completes in O(n*log n) time.
        """
        intervals = set(intervals) if intervals is not None else set()
        for iv in intervals:
            if iv.is_null():
                raise ValueError(
                    "IntervalTree: Null Interval objects not allowed in IntervalTree:"
                    " {0}".format(iv)
                )
        self.all_intervals = intervals
        self.top_node = Node.from_intervals(self.all_intervals)
        self.boundary_table = SortedDict()
        for iv in self.all_intervals:
            self._add_boundaries(iv)

    def copy(self):
        """
        Construct a new IntervalTree using shallow copies of the 
        intervals in the source tree.
        
        Completes in O(n*log n) time.
        :rtype: IntervalTree
        """
        return IntervalTree(iv.copy() for iv in self)
    
    def _add_boundaries(self, interval):
        """
        Records the boundaries of the interval in the boundary table.
        """
        begin = interval.begin
        end = interval.end
        if begin in self.boundary_table: 
            self.boundary_table[begin] += 1
        else:
            self.boundary_table[begin] = 1
        
        if end in self.boundary_table:
            self.boundary_table[end] += 1
        else:
            self.boundary_table[end] = 1
    
    def _remove_boundaries(self, interval):
        """
        Removes the boundaries of the interval from the boundary table.
        """
        begin = interval.begin
        end = interval.end
        if self.boundary_table[begin] == 1:
            del self.boundary_table[begin]
        else:
            self.boundary_table[begin] -= 1
        
        if self.boundary_table[end] == 1:
            del self.boundary_table[end]
        else:
            self.boundary_table[end] -= 1
    
    def add(self, interval):
        """
        Adds an interval to the tree, if not already present.
        
        Completes in O(log n) time.
        """
        if interval in self: 
            return

        if interval.is_null():
            raise ValueError(
                "IntervalTree: Null Interval objects not allowed in IntervalTree:"
                " {0}".format(interval)
            )

        if not self.top_node:
            self.top_node = Node.from_interval(interval)
        else:
            self.top_node = self.top_node.add(interval)
        self.all_intervals.add(interval)
        self._add_boundaries(interval)
    append = add
    
    def addi(self, begin, end, data=None):
        """
        Shortcut for add(Interval(begin, end, data)).
        
        Completes in O(log n) time.
        """
        return self.add(Interval(begin, end, data))
    appendi = addi
    
    def update(self, intervals):
        """
        Given an iterable of intervals, add them to the tree.
        
        Completes in O(m*log(n+m), where m = number of intervals to 
        add.
        """
        for iv in intervals:
            self.add(iv)

    def extend(self, intervals):
        """
        Deprecated: Replaced by update().
        """
        warn("IntervalTree.extend() has been deprecated. Consider using update() instead", DeprecationWarning)
        self.update(intervals)

    def remove(self, interval):
        """
        Removes an interval from the tree, if present. If not, raises 
        ValueError.
        
        Completes in O(log n) time.
        """
        #self.verify()
        if interval not in self:
            #print(self.all_intervals)
            raise ValueError
        self.top_node = self.top_node.remove(interval)
        self.all_intervals.remove(interval)
        self._remove_boundaries(interval)
        #self.verify()
    
    def removei(self, begin, end, data=None):
        """
        Shortcut for remove(Interval(begin, end, data)).
        
        Completes in O(log n) time.
        """
        return self.remove(Interval(begin, end, data))
    
    def discard(self, interval):
        """
        Removes an interval from the tree, if present. If not, does 
        nothing.
        
        Completes in O(log n) time.
        """
        if interval not in self:
            return
        self.all_intervals.discard(interval)
        self.top_node = self.top_node.discard(interval)
        self._remove_boundaries(interval)
    
    def discardi(self, begin, end, data=None):
        """
        Shortcut for discard(Interval(begin, end, data)).
        
        Completes in O(log n) time.
        """
        return self.discard(Interval(begin, end, data))

    def difference(self, other):
        """
        Returns a new tree, comprising all intervals in self but not
        in other.
        """
        ivs = set()
        for iv in self:
            if iv not in other:
                ivs.add(iv)
        return IntervalTree(ivs)

    def difference_update(self, other):
        """
        Removes all intervals in other from self.
        """
        for iv in other:
            self.discard(iv)

    def union(self, other):
        """
        Returns a new tree, comprising all intervals from self
        and other.
        """
        return IntervalTree(set(self).union(other))

    def intersection(self, other):
        """
        Returns a new tree of all intervals common to both self and
        other.
        """
        ivs = set()
        shorter, longer = sorted([self, other], key=len)
        for iv in shorter:
            if iv in longer:
                ivs.add(iv)
        return IntervalTree(ivs)

    def intersection_update(self, other):
        """
        Removes intervals from self unless they also exist in other.
        """
        for iv in self:
            if iv not in other:
                self.remove(iv)

    def symmetric_difference(self, other):
        """
        Return a tree with elements only in self or other but not
        both.
        """
        if not isinstance(other, set): other = set(other)
        me = set(self)
        ivs = me - other + (other - me)
        return IntervalTree(ivs)

    def symmetric_difference_update(self, other):
        """
        Throws out all intervals except those only in self or other,
        not both.
        """
        other = set(other)
        for iv in self:
            if iv in other:
                self.remove(iv)
                other.remove(iv)
        self.update(other)

    def remove_overlap(self, begin, end=None):
        """
        Removes all intervals overlapping the given point or range.
        
        Completes in O((r+m)*log n) time, where:
          * n = size of the tree
          * m = number of matches
          * r = size of the search range (this is 1 for a point)
        """
        hitlist = self.search(begin, end)
        for iv in hitlist: 
            self.remove(iv)

    def remove_envelop(self, begin, end):
        """
        Removes all intervals completely enveloped in the given range.
        
        Completes in O((r+m)*log n) time, where:
          * n = size of the tree
          * m = number of matches
          * r = size of the search range (this is 1 for a point)
        """
        hitlist = self.search(begin, end, strict=True)
        for iv in hitlist:
            self.remove(iv)

    def chop(self, begin, end, datafunc=None):
        """
        Like remove_envelop(), but trims back Intervals hanging into
        the chopped area so that nothing overlaps.
        """
        insertions = set()
        begin_hits = [iv for iv in self[begin] if iv.begin < begin]
        end_hits = [iv for iv in self[end] if iv.end > end]

        if datafunc:
            for iv in begin_hits:
                insertions.add(Interval(iv.begin, begin, datafunc(iv, True)))
            for iv in end_hits:
                insertions.add(Interval(end, iv.end, datafunc(iv, False)))
        else:
            for iv in begin_hits:
                insertions.add(Interval(iv.begin, begin, iv.data))
            for iv in end_hits:
                insertions.add(Interval(end, iv.end, iv.data))

        self.remove_envelop(begin, end)
        self.difference_update(begin_hits)
        self.difference_update(end_hits)
        self.update(insertions)

    def slice(self, point, datafunc=None):
        """
        Split Intervals that overlap point into two new Intervals. if
        specified, uses datafunc(interval, islower=True/False) to
        set the data field of the new Intervals.
        :param point: where to slice
        :param datafunc(interval, isupper): callable returning a new
        value for the interval's data field
        """
        hitlist = set(iv for iv in self[point] if iv.begin < point)
        insertions = set()
        if datafunc:
            for iv in hitlist:
                insertions.add(Interval(iv.begin, point, datafunc(iv, True)))
                insertions.add(Interval(point, iv.end, datafunc(iv, False)))
        else:
            for iv in hitlist:
                insertions.add(Interval(iv.begin, point, iv.data))
                insertions.add(Interval(point, iv.end, iv.data))
        self.difference_update(hitlist)
        self.update(insertions)

    def clear(self):
        """
        Empties the tree.

        Completes in O(1) tine.
        """
        self.__init__()

    def find_nested(self):
        """
        Returns a dictionary mapping parent intervals to sets of 
        intervals overlapped by and contained in the parent.
        
        Completes in O(n^2) time.
        :rtype: dict of [Interval, set of Interval]
        """
        result = {}
        
        def add_if_nested():
            if parent.contains_interval(child):
                if parent not in result:
                    result[parent] = set()
                result[parent].add(child)
                
        long_ivs = sorted(self.all_intervals, key=Interval.length, reverse=True)
        for i, parent in enumerate(long_ivs):
            for child in long_ivs[i + 1:]:
                add_if_nested()
        return result
    
    def overlaps(self, begin, end=None):
        """
        Returns whether some interval in the tree overlaps the given
        point or range.
        
        Completes in O(r*log n) time, where r is the size of the
        search range.
        :rtype: bool
        """
        if end is not None:
            return self.overlaps_range(begin, end)
        elif isinstance(begin, Number):
            return self.overlaps_point(begin)
        else:
            return self.overlaps_range(begin.begin, begin.end)
    
    def overlaps_point(self, p):
        """
        Returns whether some interval in the tree overlaps p.
        
        Completes in O(log n) time.
        :rtype: bool
        """
        if self.is_empty():
            return False
        return bool(self.top_node.contains_point(p))
    
    def overlaps_range(self, begin, end):
        """
        Returns whether some interval in the tree overlaps the given
        range.
        
        Completes in O(r*log n) time, where r is the range length and n
        is the table size.
        :rtype: bool
        """
        if self.is_empty():
            return False
        elif self.overlaps_point(begin):
            return True
        return any(
            self.overlaps_point(bound) 
            for bound in self.boundary_table 
            if begin <= bound < end
        )
    
    def split_overlaps(self):
        """
        Finds all intervals with overlapping ranges and splits them
        along the range boundaries.
        
        Completes in worst-case O(n^2*log n) time (many interval 
        boundaries are inside many intervals), best-case O(n*log n)
        time (small number of overlaps << n per interval).
        """
        if not self:
            return
        if len(self.boundary_table) == 2:
            return

        bounds = sorted(self.boundary_table)  # get bound locations

        new_ivs = set()
        for lbound, ubound in zip(bounds[:-1], bounds[1:]):
            for iv in self[lbound]:
                new_ivs.add(Interval(lbound, ubound, iv.data))

        self.__init__(new_ivs)

    def items(self):
        """
        Constructs and returns a set of all intervals in the tree. 
        
        Completes in O(n) time.
        :rtype: set of Interval
        """
        return set(self.all_intervals)
    
    def is_empty(self):
        """
        Returns whether the tree is empty.
        
        Completes in O(1) time.
        :rtype: bool
        """
        return 0 == len(self)

    def search(self, begin, end=None, strict=False):
        """
        Returns a set of all intervals overlapping the given range. Or,
        if strict is True, returns the set of all intervals fully
        contained in the range [begin, end].
        
        Completes in O(m + k*log n) time, where:
          * n = size of the tree
          * m = number of matches
          * k = size of the search range (this is 1 for a point)
        :rtype: set of Interval
        """
        root = self.top_node
        if not root:
            return set()
        if end is None:
            try:
                iv = begin
                return self.search(iv.begin, iv.end, strict=strict)
            except:
                return root.search_point(begin, set())
        elif begin >= end:
            return set()
        else:
            result = root.search_point(begin, set())

            boundary_table = self.boundary_table
            bound_begin = boundary_table.bisect_left(begin)
            bound_end = boundary_table.bisect_left(end)  # exclude final end bound
            result.update(root.search_overlap(
                # slice notation is slightly slower
                boundary_table.iloc[index] for index in xrange(bound_begin, bound_end)
            ))

            # TODO: improve strict search to use node info instead of less-efficient filtering
            if strict:
                result = set(
                    iv for iv in result
                    if iv.begin >= begin and iv.end <= end
                )
            return result
    
    def begin(self):
        """
        Returns the lower bound of the first interval in the tree.
        
        Completes in O(n) time.
        :rtype: Number
        """
        if not self.boundary_table:
            return 0
        return min(self.boundary_table)
    
    def end(self):
        """
        Returns the upper bound of the last interval in the tree.
        
        Completes in O(n) time.
        :rtype: Number
        """
        if not self.boundary_table:
            return 0
        return max(self.boundary_table)
    
    def print_structure(self, tostring=False):
        """
        ## FOR DEBUGGING ONLY ##
        Pretty-prints the structure of the tree. 
        If tostring is true, prints nothing and returns a string.
        :rtype: None or str
        """
        if self.top_node:
            return self.top_node.print_structure(tostring=tostring)
        else:
            result = "<empty IntervalTree>"
            if not tostring:
                print(result)
            else:
                return result

    def score(self, full_report=False):
        """
        Returns a number between 0 and 1, indicating how suboptimal the tree
        is. The lower, the better. Roughly, this number represents the
        fraction of flawed Intervals in the tree.
        :rtype: float
        """
        if len(self) <= 2:
            return 0.0

        n = len(self)
        m = self.top_node.count_nodes()

        def s_center_score():
            """
            Returns a normalized score, indicating roughly how many times
            intervals share s_center with other intervals. Output is full-scale
            from 0 to 1.
            :rtype: float
            """
            raw = n - m
            maximum = n - 1
            return raw / float(maximum)

        report = {
            "depth": self.top_node.depth_score(n, m),
            "s_center": s_center_score(),
        }
        cumulative = max(report.values())
        report["_cumulative"] = cumulative
        if full_report:
            return report
        return cumulative

    def __getitem__(self, index):
        """
        Returns a set of all intervals overlapping the given index or 
        slice.
        
        Completes in O(k * log(n) + m) time, where:
          * n = size of the tree
          * m = number of matches
          * k = size of the search range (this is 1 for a point)
        :rtype: set of Interval
        """
        try:
            start, stop = index.start, index.stop
            if start is None:
                start = self.begin()
                if stop is None:
                    return set(self)
            if stop is None:
                stop = self.end()
            return self.search(start, stop)
        except AttributeError:
            return self.search(index)
    
    def __setitem__(self, index, value):
        """
        Adds a new interval to the tree. A shortcut for
        add(Interval(index.start, index.stop, value)).
        
        If an identical Interval object with equal range and data 
        already exists, does nothing.
        
        Completes in O(log n) time.
        """
        self.addi(index.start, index.stop, value)

    def __delitem__(self, point):
        """
        Delete all items overlapping point.
        """
        self.remove_overlap(point)

    def __contains__(self, item):
        """
        Returns whether item exists as an Interval in the tree.
        This method only returns True for exact matches; for
        overlaps, see the overlaps() method.
        
        Completes in O(1) time.
        :rtype: bool
        """
        # Removed point-checking code; it might trick the user into
        # thinking that this is O(1), which point-checking isn't.
        #if isinstance(item, Interval):
        return item in self.all_intervals
        #else:
        #    return self.contains_point(item)
    
    def containsi(self, begin, end, data=None):
        """
        Shortcut for (Interval(begin, end, data) in tree).
        
        Completes in O(1) time.
        :rtype: bool
        """
        return Interval(begin, end, data) in self
    
    def __iter__(self):
        """
        Returns an iterator over all the intervals in the tree.
        
        Completes in O(1) time.
        :rtype: collections.Iterable[Interval]
        """
        return self.all_intervals.__iter__()
    iter = __iter__
    
    def __len__(self):
        """
        Returns how many intervals are in the tree.
        
        Completes in O(1) time.
        :rtype: int
        """
        return len(self.all_intervals)
    
    def __eq__(self, other):
        """
        Whether two IntervalTrees are equal.
        
        Completes in O(n) time if sizes are equal; O(1) time otherwise.
        :rtype: bool
        """
        return (
            isinstance(other, IntervalTree) and 
            self.all_intervals == other.all_intervals
        )
    
    def __repr__(self):
        """
        :rtype: str
        """
        ivs = sorted(self)
        if not ivs:
            return "IntervalTree()"
        else:
            return "IntervalTree({0})".format(ivs)

    __str__ = __repr__

    def __reduce__(self):
        """
        For pickle-ing.
        :rtype: tuple
        """
        return IntervalTree, (sorted(self.all_intervals),)