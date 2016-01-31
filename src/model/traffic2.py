__author__ = 'Rakesh Kumar'

from collections import namedtuple
from segment_tree import SegmentTree
from segment_tree import TwoLevelSegmentTree

class ContourEndPoint(namedtuple('ContourEndPoint', ['x', 'y', 'other_y'])):
    __slots__ = ()

    def __new__(cls, x, y, other_y):
        return super(ContourEndPoint, cls).__new__(cls, x, y, other_y)


class VerticalEdge(namedtuple('VerticalEdge', ['x', 'y_b', 'y_t'])):
    __slots__ = ()

    def __new__(cls, x, y_b, y_t):
        return super(VerticalEdge, cls).__new__(cls, x, y_b, y_t)


class HorizontalEdge(namedtuple('HorizontalEdge', ['y', 'x_l', 'x_r'])):
    __slots__ = ()

    def __new__(cls, y, x_l, x_r):
        return super(HorizontalEdge, cls).__new__(cls, y, x_l, x_r)


class Interval(namedtuple('IntervalBase', ['begin', 'end', 'data'])):
    __slots__ = ()

    def __new__(cls, begin, end, data=None):
        return super(Interval, cls).__new__(cls, begin, end, data)

class Rectangle():

    def __init__(self, x1, x2, y1, y2, z1=0, z2=0):

        self.x = Interval(x1, x2)
        self.y = Interval(y1, y2)
        self.z = Interval(z1, z2)

def measure_of_union_of_intervals(interval_list):

    X = []
    m = 0
    c = 0

    for interval in interval_list:
        X.append((interval.begin, 'begin'))
        X.append((interval.end, 'end'))

    # Prepare X
    X = sorted(X, key=lambda tup: tup[0])
    X.insert(0, X[0])

    for i in xrange(1, len(X)):
        print i

        if c != 0:
            m = m + X[i][0] - X[i-1][0]

        if X[i][1] == 'begin':
            c += 1
        else:
            c -= 1

    return m

def measure_of_union_of_rectangles(rectangle_list):

    X = []
    Y = []
    m = 0

    for rectangle in rectangle_list:
        X.append((rectangle.x.begin, 'begin', rectangle.y.begin, rectangle.y.end))
        X.append((rectangle.x.end, 'end', rectangle.y.begin, rectangle.y.end))

        Y.append((rectangle.y.begin, 'begin'))
        Y.append((rectangle.y.end, 'end'))

    # Prepare X
    X = sorted(X, key=lambda tup: tup[0])
    X.insert(0, X[0])

    # Prepare Segment Tree for Y
    Y = sorted(Y, key=lambda tup: tup[0])
    st = SegmentTree(Y[0][0], Y[len(Y) - 1][0])

    for i in xrange(1, len(X)):
        m = m + st.root.m * (X[i][0] - X[i-1][0])

        if X[i][1] == 'begin':
            st.root.insert(X[i][2], X[i][3])
        else:
            st.root.delete(X[i][2], X[i][3])

    return m

def measure_of_union_of_rectangles_3d(rectangle_list):

    X = []
    Y = []
    Z = []

    m = 0

    for rectangle in rectangle_list:
        X.append((rectangle.x.begin, 'begin', rectangle.y.begin, rectangle.y.end, rectangle.z.begin, rectangle.z.end))
        X.append((rectangle.x.end, 'end', rectangle.y.begin, rectangle.y.end, rectangle.z.begin, rectangle.z.end))

        Y.append((rectangle.y.begin, 'begin'))
        Y.append((rectangle.y.end, 'end'))

        Z.append((rectangle.z.begin, 'begin'))
        Z.append((rectangle.z.end, 'end'))

    # Prepare X
    X = sorted(X, key=lambda tup: tup[0])
    X.insert(0, X[0])

    # Prepare Multi-level Segment Tree for Y-Z
    Y = sorted(Y, key=lambda tup: tup[0])
    Z = sorted(Z, key=lambda tup: tup[0])

    st_yz = TwoLevelSegmentTree(Y[0][0], Y[len(Y) - 1][0], Z[0][0], Z[len(Z) - 1][0])

    for i in xrange(1, len(X)):

        # Take current contributions along both y and z dimensions and multiply with x

        x_contr = X[i][0] - X[i-1][0]

        print X[i][2], X[i][3], X[i][4], X[i][5]

        print "yz contribution is: ", st_yz.root.m2

        print "total_contribution between x =", X[i-1][0], "and x =", X[i][0], "is:", x_contr * st_yz.root.m2

        m = m + x_contr * st_yz.root.m2

        if X[i][1] == 'begin':
            st_yz.root.insert(X[i][2], X[i][3], X[i][4], X[i][5])
        else:
            st_yz.root.delete(X[i][2], X[i][3], X[i][4], X[i][5])

    return m

def perimeter_of_union_of_rectangles(rectangle_list):
    X = []
    Y = []
    p = 0
    m_zero = 0

    for rectangle in rectangle_list:
        X.append((rectangle.x.begin, 'begin', rectangle.y.begin, rectangle.y.end))
        X.append((rectangle.x.end, 'end', rectangle.y.begin, rectangle.y.end))

        Y.append((rectangle.y.begin, 'begin'))
        Y.append((rectangle.y.end, 'end'))

    # Prepare X
    X = sorted(X, key=lambda tup: tup[0])
    X.insert(0, X[0])

    # Prepare Segment Tree for Y
    Y = sorted(Y, key=lambda tup: tup[0])
    st = SegmentTree(Y[0][0], Y[len(Y) - 1][0])

    for i in xrange(1, len(X)):

        alpha_star = st.root.alpha

        if X[i][1] == 'begin':
            st.root.insert(X[i][2], X[i][3])
        else:
            st.root.delete(X[i][2], X[i][3])

        m_star = st.root.m
        p = p + alpha_star * (X[i][0] - X[i-1][0]) + abs(m_star - m_zero)
        m_zero = m_star

    return p

def accumulate_vertical_edges_and_endpoints(A, vertical_edges, abscissa, stack):
    ordinate_i = 0
    while ordinate_i < len(stack) - 1:

        if stack[ordinate_i] < stack[ordinate_i + 1] + 1:
            vep1 = ContourEndPoint(abscissa, stack[ordinate_i], stack[ordinate_i + 1])
            vep2 = ContourEndPoint(abscissa, stack[ordinate_i + 1], stack[ordinate_i])
            ve = VerticalEdge(abscissa, stack[ordinate_i], stack[ordinate_i + 1])
        else:
            vep1 = ContourEndPoint(abscissa, stack[ordinate_i], stack[ordinate_i + 1])
            vep2 = ContourEndPoint(abscissa, stack[ordinate_i + 1], stack[ordinate_i])
            ve = VerticalEdge(abscissa, stack[ordinate_i + 1], stack[ordinate_i])

        ordinate_i += 2
        A.append(vep1)
        A.append(vep2)
        vertical_edges.append(ve)

def contour_of_union_of_rectangles(rectangle_list):
    X = []
    Y = []

    for rectangle in rectangle_list:
        X.append((rectangle.x.begin, 'begin', rectangle.y.begin, rectangle.y.end))
        X.append((rectangle.x.end, 'end', rectangle.y.begin, rectangle.y.end))

        Y.append((rectangle.y.begin, 'begin'))
        Y.append((rectangle.y.end, 'end'))

    # Prepare X
    X = sorted(X, key=lambda tup: tup[0])

    # Prepare Segment Tree for Y
    Y = sorted(Y, key=lambda tup: tup[0])
    st = SegmentTree(Y[0][0], Y[len(Y) - 1][0])

    # A contains all vertical edges
    A = []
    horizontal_edges = []
    vertical_edges = []

    for i in xrange(0, len(X)):

        if X[i][1] == 'begin':
            stack = []
            st.root.contr(X[i][2], X[i][3], stack)
            accumulate_vertical_edges_and_endpoints(A, vertical_edges, X[i][0], stack)

            st.root.insert(X[i][2], X[i][3])
        else:
            st.root.delete(X[i][2], X[i][3])

            stack = []
            st.root.contr(X[i][2], X[i][3], stack)
            accumulate_vertical_edges_and_endpoints(A, vertical_edges, X[i][0], stack)

    # Perform a lexicographic sort on A, first on ordinates, then on abscissa
    A.sort(key=lambda endpoint: (endpoint.y, endpoint.x))

    # Pick out all the horizontal and vertical edges
    for k in xrange(len(A)/2):

        # Report edges only when there is something there...

        if abs(A[2*k].x - A[2*k + 1].x) > 0:

            # Two consecutive endpoints at 2k and 2k + 1 give rise to one horizontal edge
            horizontal_edges.append(HorizontalEdge(A[2*k].y,  A[2*k].x,  A[2*k + 1].x))

    return vertical_edges, horizontal_edges

def main():

    #interval_list = [Interval(1, 2), Interval(1, 2)]
    #measure_of_union_of_intervals(interval_list)

    # rectangle_list = [Rectangle(1, 3, 1, 3), Rectangle(2, 4, 2, 4), Rectangle(5, 7, 5, 7)]
    # m = measure_of_union_of_rectangles(rectangle_list)
    # print m

    # #rectangle_list = [Rectangle(1, 3, 1, 3), Rectangle(2, 4, 2, 4)] # 12
    # #rectangle_list = [Rectangle(1, 3, 1, 3), Rectangle(2, 5, 2, 5)] # 16
    # #rectangle_list = [Rectangle(1, 3, 1, 3), Rectangle(5, 7, 10, 32)] # 56
    # rectangle_list = [Rectangle(1, 3, 1, 3), Rectangle(2, 4, 2, 4), Rectangle(5, 7, 5, 7)] # 20
    # p = perimeter_of_union_of_rectangles(rectangle_list)
    # print p

    #rectangle_list = [Rectangle(1, 3, 1, 3)]
    # rectangle_list = [Rectangle(0, 10, 0, 10), Rectangle(1, 3, 1, 3), Rectangle(2, 4, 2, 4), Rectangle(3, 5, 3, 5)]
    # rectangle_list = [Rectangle(1, 3, 1, 3), Rectangle(5, 7, 5, 7)]
    # rectangle_list = [Rectangle(1, 3, 1, 3), Rectangle(2, 4, 2, 4), Rectangle(3, 5, 3, 5)]
    #rectangle_list = [Rectangle(1, 3, 1, 3), Rectangle(2, 4, 2, 4)]

    # rectangle_list = [Rectangle(1, 3, 1, 3), Rectangle(2, 4, 2, 4), Rectangle(1, 5, 2, 4)]
    # vertical_edges, horizontal_edgs = contour_of_union_of_rectangles(rectangle_list)
    # print vertical_edges, horizontal_edgs

    ## Single Box Case # 8
    #rectangle_list = [Rectangle(1, 3, 1, 3, 1, 3)]

    ## Two separate Boxes case # 16
    #rectangle_list = [Rectangle(1, 3, 1, 3, 1, 3), Rectangle(5, 7, 5, 7, 5, 7)]

    ## One big box containing another box # 64
    #rectangle_list = [Rectangle(1, 5, 1, 5, 1, 5), Rectangle(2, 4, 2, 4, 2, 4)]

    # One box intersecting with another box of only x axis changing # 30
    #rectangle_list = [Rectangle(1, 4, 1, 4, 1, 3), Rectangle(3, 6, 1, 4, 1, 3)]

    # One box intersecting with another box of both x and y axis changing # 34
    #rectangle_list = [Rectangle(1, 4, 1, 4, 1, 3), Rectangle(3, 6, 3, 6, 1, 3)]

    # One box intersecting with another box with only z axis changing # 27
    #rectangle_list = [Rectangle(1, 4, 1, 4, 1, 3), Rectangle(1, 4, 1, 4, 2, 4)]

    #One box intersecting with another box with y and z axis changing # 24 - 3 = 21
    #rectangle_list = [Rectangle(1, 4, 1, 3, 1, 3), Rectangle(1, 4, 2, 4, 2, 4)]

    # Canonical Example with all three axes moving # 15
    rectangle_list = [Rectangle(1, 3, 1, 3, 1, 3), Rectangle(2, 4, 2, 4, 2, 4)]

    m = measure_of_union_of_rectangles_3d(rectangle_list)

    print m



if __name__ == "__main__":
    main()

