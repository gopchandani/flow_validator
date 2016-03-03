__author__ = 'Rakesh Kumar'

class TrafficPath(object):

    def __init__(self, nodes=[], path_edges=[]):
        self.path_nodes = nodes
        self.path_edges = path_edges

    def path_length(self):
        return len(self.path_nodes)

    def __eq__(self, other):

        equal_paths = True

        if len(self.path_nodes) == len(other.path_nodes):
            for i in range(len(self.path_nodes)):
                if self.path_nodes[i] != other.path_nodes[i]:
                    equal_paths = False
                    break
        else:
            equal_paths = False

        return equal_paths

    def __str__(self):
        path_str = ''

        for i in range(len(self.path_nodes) - 1):
            path_str += str(self.path_nodes[i]) + ' -> '

        path_str += str(self.path_nodes[len(self.path_nodes) - 1])

        for edge, enabling_edge_data_list in self.path_edges:
            path_str += "\n" + str(edge[0]) + "->" + str(edge[1]) + "\n"


        return path_str

    def __iter__(self):
        for node in self.path_nodes:
            yield node