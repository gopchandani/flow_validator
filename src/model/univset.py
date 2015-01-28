__author__ = 'Rakesh Kumar'


class univset(object):
    def __init__(self):
        self._exceptions = set()

    def __sub__(self, other):
        S = univset()
        if type(other) == set:
            S._exceptions = self._exceptions | other
            return S
        else:
            S._exceptions = self._exceptions | other._exceptions
            return S

    def __rsub__(self, other):
        return other & self._exceptions

    def __contains__(self, obj):
        return not obj in self._exceptions

    def __and__(self, other):
        return other - self._exceptions

    def __rand__(self, other):
        return other - self._exceptions

    def __repr__(self):
        if self._exceptions == set():
            return "ANY"
        else:
            return "ANY - %s"%self._exceptions

    def __or__(self, other):
        S = univset()
        S._exceptions = self._exceptions - other
        return S

    def __xor__(self, other):
        return (self - other) | (other - self)

    def add(self, elem):
        if elem in self._exceptions:
            self._exceptions.remove(elem)

    def update(self, elem):
        self._exceptions = self._exceptions - other

    def __ror__(self, other):
        return self.__or__(other)

    def union(self, other):
        return self.__or__(other)

    def difference(self, other):
        return self.__sub__(other)

    def intersection(self, other):
        return self.__and__(other)

    def symmetric_exceptionserence(self, other):
        return self.__xor__(other)

    def issubset(self, other):
        if type(other) == set:
            return False
        if issubset(other._exceptions, self._exceptions):
            return True
        return False

    def issuperset(self, other):
        if self._exceptions & other:
            return False
        return True

    def __lt__(self, other):
        return self.issubset(other)

    def __eq__(self, other):
        if type(other) == set:
            return False
        try:
            return self._exceptions == other._exceptions
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __gt__(self, other):
        return self.issuperset(other)

    def __gt__(self, other):
        return self.issuperset(other) or self == other


def main():

    ANY = univset()
    NON_DIGITS = ANY - set(range(9))

    print 8 not in NON_DIGITS
    print 0 not in NON_DIGITS
    print 'a' in NON_DIGITS
    print 0 in NON_DIGITS | set([0])


if __name__ == "__main__":
    main()