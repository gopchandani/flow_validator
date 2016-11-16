CONNECTIVITY_CONSTRAINT = "Connectivity"
PATH_LENGTH_CONSTRAINT = "PathLength"
LINK_EXCLUSIVITY_CONSTRAINT = "LinkExclusivity"


class PolicyStatement(object):

    def __init__(self, src_zone, dst_zone, traffic, constraints, k):
        self.src_zone = src_zone
        self.dst_zone = dst_zone
        self.traffic = traffic
        self.constraints = constraints
        self.k = k
