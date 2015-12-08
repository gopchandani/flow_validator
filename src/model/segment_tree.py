__author__ = 'Rakesh Kumar'

class SegmentTreeNode:

    def __init__(self, low, high):

        self.low = low
        self.high = high

        self.lc = None
        self.rc = None

        # TODO: Attributes at this node as a dict

        # Book for intervals stored
        self.stored_intervals = []

        # General attributes/properties
        self.C = 0

        # Specific to measure problem
        self.m = 0

        # Specific to perimeter problem
        self.lbd = 0
        self.rbd = 0
        self.alpha = 0

        # Specific to contour problem
        self.status = 'empty'

    def insert(self, low, high):
        if low <= self.low and self.high <= high:
            self.stored_intervals.append((low, high))
            self.C += 1
        else:
            if low < (self.low + self.high) / 2:
                self.lc.insert(low, high)
            if (self.low + self.high) / 2 < high:
                self.rc.insert(low, high)

        self.update()

    def delete(self, low, high):
        if low <= self.low and self.high <= high:
            self.C -= 1
            self.stored_intervals = filter(lambda x: not (x[0] == low and x[1] == high), self.stored_intervals)
        else:
            if low < (self.low + self.high) / 2:
                self.lc.delete(low, high)
            if (self.low + self.high) / 2 < high:
                self.rc.delete(low, high)

        self.update()

    def query(self, q, overlapping_intervals):

        overlapping_intervals.extend(self.stored_intervals)

        if self.lc and self.rc:
            if q >= self.lc.low and q <= self.lc.high:
                self.lc.query(q, overlapping_intervals)
            else:
                self.rc.query(q, overlapping_intervals)

    def update(self):

        # Update m
        if self.C != 0:
            self.m = self.high - self.low
        else:
            if (self.lc and self.rc):
                self.m = self.lc.m + self.rc.m
            else:
                self.m = 0

        # Update lbd, rbd and alpha
        if self.C > 0:
            self.alpha = 2
            self.lbd = 1
            self.rbd = 1
        else:
            if self.lc and self.rc:
                self.alpha = self.lc.alpha + self.rc.alpha - 2 * self.lc.rbd * self.rc.lbd
                self.lbd = self.lc.lbd
                self.rbd = self.rc.rbd
            else:
                self.alpha = 0
                self.lbd = 0
                self.rbd = 0

        # Update status
        if self.C > 0:
            self.status = 'full'
        else:
            if self.lc and self.rc:
                if self.lc.status == 'empty' and self.rc.status == 'empty':
                    self.status = 'empty'
                else:
                    self.status = 'partial'
            else:
                self.status = 'empty'

    # For contours, this computes the contribution of a given vertex
    def contr(self, low, high, stack):

        if self.status != 'full':

            if (low <= self.low and self.high <= high) and (self.status == 'empty'):
                if stack and self.low == stack[len(stack) - 1]:
                    stack.pop()
                else:
                    stack.append(self.low)
                stack.append(self.high)
            else:

                if self.lc and self.rc:
                    if low < (self.low + self.high) / 2:
                        self.lc.contr(low, high, stack)
                    if (self.low + self.high) / 2 < high:
                        self.rc.contr(low, high, stack)

class SegmentTree:

    def __init__(self, neg_inf, pos_inf):

        self.neg_inf = neg_inf
        self.pos_inf = pos_inf

        self.root = self.build_seg_tree(self.neg_inf, self.pos_inf)

    def build_seg_tree(self, low, high):

        subtree = SegmentTreeNode(low, high)

        if high - low > 1:
            subtree.lc = self.build_seg_tree(low, (low + high)/2)
            subtree.rc = self.build_seg_tree((low + high)/2, high)

        return subtree

class TwoLevelSegmentTreeNode:

    def __init__(self, low, high):

        self.low = low
        self.high = high

        self.lc = None
        self.rc = None

        # TODO: Attributes at this node as a dict
        # General attributes/properties
        self.C = 0
        
        # Book for intervals stored
        self.stored_intervals = []
        
        # Specific to measure problem
        self.m2 = 0

        # st for leaves
        self.st = None

    def insert(self, low_1, high_1, low_2, high_2):

        if low_1 <= self.low and self.high <= high_1:
            self.st.root.insert(low_2, high_2)
            
            self.stored_intervals.append((low_1, high_1))
            self.C += 1
            
        else:
            if low_1 < (self.low + self.high) / 2:
                self.lc.insert(low_1, high_1, low_2, high_2)

            if (self.low + self.high) / 2 < high_1:
                self.rc.insert(low_1, high_1, low_2, high_2)

        self.update()

    def delete(self, low_1, high_1, low_2, high_2):

        if low_1 <= self.low and self.high <= high_1:
            self.st.root.delete(low_2, high_2)
            
            self.stored_intervals = filter(lambda x: not (x[0] == low_1 and x[1] == high_1), self.stored_intervals)
            self.C -= 1
        else:
            if low_1 < (self.low + self.high) / 2:
                self.lc.delete(low_1, high_1, low_2, high_2)

            if (self.low + self.high) / 2 < high_1:
                self.rc.delete(low_1, high_1, low_2, high_2)

        self.update()

    def query(self, q1, q2, overlapping_rectangles):

        # See what is going on 2nd dimension
        overlapping_intervals = []
        self.st.root.query(q2, overlapping_intervals)

        # If there is 'stuff' on second dimension for q2
        if overlapping_intervals:
            for oi in overlapping_intervals:
                for si in self.stored_intervals:
                    overlapping_rectangles.append((si[0], si[1], oi[0], oi[1]))

        if self.lc and self.rc:
            if q1 >= self.lc.low and q1 <= self.lc.high:
                self.lc.query(q1, q2, overlapping_rectangles)
            else:
                self.rc.query(q1, q2, overlapping_rectangles)

    def update(self):

        # Update m and m2

        # If there has been an interval that covered this node entirely...
        if self.C != 0:
            self.m2 = (self.high - self.low) * self.st.root.m

        # If not, then see if this is a leaf node or not,
        else:
            # If not a leaf, its measure is sum of its children's measure
            if (self.lc and self.rc):
                self.m2 = self.lc.m2 + self.rc.m2

            # If it is a leaf, then its measure is zero
            else:
                self.m2 = 0


class TwoLevelSegmentTree:

    def __init__(self, neg_inf_1, pos_inf_1, neg_inf_2, pos_inf_2):

        self.neg_inf_1 = neg_inf_1
        self.pos_inf_1 = pos_inf_1

        self.neg_inf_2 = neg_inf_2
        self.pos_inf_2 = pos_inf_2

        self.root = self.build_seg_tree(self.neg_inf_1, self.pos_inf_1)

    def build_seg_tree(self, low_1, high_1):

        subtree_root = TwoLevelSegmentTreeNode(low_1, high_1)

        if high_1 - low_1 > 1:
            subtree_root.lc = self.build_seg_tree(low_1, (low_1 + high_1)/2)
            subtree_root.rc = self.build_seg_tree((low_1 + high_1)/2, high_1)

            subtree_root.st = SegmentTree(self.neg_inf_2, self.pos_inf_2)
            subtree_root.st = SegmentTree(self.neg_inf_2, self.pos_inf_2)

        else:
            subtree_root.st = SegmentTree(self.neg_inf_2, self.pos_inf_2)

        return subtree_root

def main():

    # st = SegmentTree(1, 257)
    # st.root.insert(74, 107)
    # st.root.delete(74, 107)
    # st.root.insert(39, 104)
    # st.root.insert(99, 101)
    # st.root.insert(230, 244)
    #
    # query_interval_output = []
    # st.root.query(100, query_interval_output)
    # print query_interval_output

    # mlst = TwoLevelSegmentTree(1, 257, 1, 257)
    #
    # mlst.root.insert(74, 107, 74, 107)
    # mlst.root.insert(20, 40, 20, 40)
    # mlst.root.insert(30, 80, 30, 80)
    # mlst.root.delete(30, 80, 30, 80)
    #
    # query_rectangle_output = []
    # mlst.root.query(31, 31, query_rectangle_output)
    # print query_rectangle_output
    #

    mlst = TwoLevelSegmentTree(0, 10, 0, 10)

    mlst.root.insert(0, 10, 0, 10)
    mlst.root.insert(7, 10, 7, 10)
    mlst.root.insert(0, 4, 0, 3)
    mlst.root.insert(1, 5, 1, 4)

    query_rectangle_output = []
    mlst.root.query(0.5, 3, query_rectangle_output)
    print query_rectangle_output

    query_rectangle_output = []
    mlst.root.query(2, 2, query_rectangle_output)
    print query_rectangle_output

    query_rectangle_output = []
    mlst.root.query(8, 8, query_rectangle_output)
    print query_rectangle_output

if __name__ == "__main__":
    main()

