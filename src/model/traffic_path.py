__author__ = 'Rakesh Kumar'

class TrafficPath(object):

    def __init__(self, elems=[]):
        self.path_elements = elems

    def add_to_path(self, elements):
        self.path_elements.extend(elements)

    def path_length(self):
        return len(self.path_elements)

    def __eq__(self, other):

        equal_paths = True

        if len(self.path_elements) == len(other.path_elements):
            for i in range(len(self.path_elements)):
                if self.path_elements[i] != other.path_elements[i]:
                    equal_paths = False
                    break
        else:
            equal_paths = False

        return equal_paths

    def __iter__(self):
        for elem in self.path_elements:
            yield elem