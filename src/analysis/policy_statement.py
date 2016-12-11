CONNECTIVITY_CONSTRAINT = "Connectivity"
PATH_LENGTH_CONSTRAINT = "PathLength"
LINK_EXCLUSIVITY_CONSTRAINT = "LinkExclusivity"


class PolicyConstraint(object):
    def __init__(self, constraint_type, constraint_params):
        self.constraint_type = constraint_type
        self.constraint_params = constraint_params


class PolicyViolation(object):
    def __init__(self, lmbda, src_port, dst_port, constraint, counter_example):
        self.lmbda = lmbda
        self.src_port = src_port
        self.dst_port = dst_port
        self.constraint = constraint
        self.counter_example = counter_example


class PolicyStatement(object):

    def __init__(self, network_graph, src_zone, dst_zone, traffic, constraints, k):
        self.network_graph = network_graph
        self.src_zone = src_zone
        self.dst_zone = dst_zone
        self.traffic = traffic
        self.constraints = constraints
        self.k = k

        # Convert constraint links to NetworkGraphLinkData objects
        for c in self.constraints:
            if c.constraint_type == LINK_EXCLUSIVITY_CONSTRAINT:
                converted_links = []
                for link in c.constraint_params:
                    converted_links.append(self.network_graph.get_link_data(link[0], link[1]))

                c.constraint_params = converted_links

