import sys
import itertools

sys.path.append("./")

from collections import defaultdict
from model.network_port_graph import NetworkPortGraph
from model.traffic import Traffic
from util import get_specific_traffic
from util import get_admitted_traffic, get_paths
from analysis.policy_statement import CONNECTIVITY_CONSTRAINT, ISOLATION_CONSTRAINT
from analysis.policy_statement import PATH_LENGTH_CONSTRAINT, LINK_AVOIDANCE_CONSTRAINT
from analysis.policy_statement import PolicyViolation

__author__ = 'Rakesh Kumar'


class FlowValidator(object):

    def __init__(self, network_graph, report_active_state=True):
        self.network_graph = network_graph
        self.port_graph = NetworkPortGraph(network_graph, report_active_state)

    def init_network_port_graph(self):
        self.port_graph.init_network_port_graph()
        self.port_graph.init_network_admitted_traffic()

    def de_init_network_port_graph(self):
        self.port_graph.de_init_network_port_graph()

    def initialize_per_link_traffic_paths(self, verbose=False):

        for ld in self.network_graph.get_switch_link_data():
            ld.traffic_paths = []

        for src_h_id in self.network_graph.host_ids:
            for dst_h_id in self.network_graph.host_ids:

                if src_h_id == dst_h_id:
                    continue

                src_host_obj = self.network_graph.get_node_object(src_h_id)
                dst_host_obj = self.network_graph.get_node_object(dst_h_id)

                specific_traffic = get_specific_traffic(self.network_graph, src_h_id, dst_h_id)

                all_paths = get_paths(self.port_graph,
                                      specific_traffic,
                                      src_host_obj.switch_port,
                                      dst_host_obj.switch_port)

                for path in all_paths:
                    if verbose:
                        print "src_h_id:", src_h_id, "dst_h_id:", dst_h_id, "path:", path

                    path_links = path.get_path_links()
                    for ld in path_links:

                        # Avoid adding the same path twice for cases when a link is repeated
                        if path not in ld.traffic_paths:
                            ld.traffic_paths.append(path)

    def port_pair_iter(self, src_zone, dst_zone):

        for src_port in src_zone:
            for dst_port in dst_zone:

                if src_port == dst_port:
                    continue

                # Doing validation only between ports that have hosts attached with them
                if not src_port.attached_host or not dst_port.attached_host:
                    continue

                yield src_port, dst_port

    def is_node_in_zone(self, node, zone, as_ingress_egress):

        result = False

        for port in zone:

            if as_ingress_egress == "ingress":
                if port.network_port_graph_ingress_node == node:
                    result = True
                    break

            elif as_ingress_egress == "egress":

                if port.network_port_graph_egress_node == node:
                    result = True
                    break
            else:
                raise Exception("Unknown as_ingress_egress")

        return result

    def validate_connectvity_constraint(self, src_port, dst_port, traffic):

        at = get_admitted_traffic(self.port_graph, src_port, dst_port)
        counter_example = None

        if not at.is_empty():
            if at.is_subset_traffic(traffic):
                traffic_paths = get_paths(self.port_graph, traffic, src_port, dst_port)

                if traffic_paths:
                    satisfies = True
                else:
                    #TODO: This needs fixing (and a test)
                    satisfies = False
                    counter_example = Traffic()
            else:
                #print "src_port:", src_port, "dst_port:", dst_port, "at does not pass traffic check."
                satisfies = False
                counter_example = at

        else:
            #print "src_port:", src_port, "dst_port:", dst_port, "at is empty."
            satisfies = False
            counter_example = at

        return satisfies, counter_example

    def validate_isolation_constraint(self, src_port, dst_port, traffic):

        at = get_admitted_traffic(self.port_graph, src_port, dst_port)
        counter_example = None
        satisfies = True

        if not at.is_empty():
            if at.is_subset_traffic(traffic):
                traffic_paths = get_paths(self.port_graph, traffic, src_port, dst_port)

                if traffic_paths:
                    satisfies = False
                    counter_example = at

        return satisfies, counter_example

    def validate_path_length_constraint(self, src_port, dst_port, traffic, l):

        satisfies = True
        counter_example = None

        traffic_paths = get_paths(self.port_graph, traffic, src_port, dst_port)

        for path in traffic_paths:
            if len(path) > l:
                #print "src_port:", src_port, "dst_port:", dst_port, "Path does not fit in specified limit:", path
                satisfies = False
                counter_example = path
                break

        return satisfies, counter_example

    def validate_link_avoidance(self, src_zone, dst_zone, traffic, el):
        satisfies = True
        counter_example = None

        for l in el:

            # Check to see if any of the paths crossing this link are all from src_port to dst_port and vice versa
            for path in l.traffic_paths:

                if self.is_node_in_zone(path.src_node, src_zone, "ingress") and \
                        self.is_node_in_zone(path.dst_node, dst_zone, "egress"):

                    #print "Against policy, found path:", path, "on link:", l
                    satisfies = False
                    counter_example = path
                    break

        return satisfies, counter_example

    def validate_policy_cases(self, validation_map, lmbda):

        v = []

        for src_port, dst_port in validation_map:

            for ps in validation_map[(src_port, dst_port)]:

                # Setup the appropriate filter
                ps.traffic.set_field("ethernet_source", int(src_port.attached_host.mac_addr.replace(":", ""), 16))
                ps.traffic.set_field("ethernet_destination", int(dst_port.attached_host.mac_addr.replace(":", ""), 16))
                ps.traffic.set_field("in_port", int(src_port.port_number))

                for constraint in ps.constraints:

                    if constraint.constraint_type == CONNECTIVITY_CONSTRAINT:
                        satisfies, counter_example = self.validate_connectvity_constraint(src_port,
                                                                                          dst_port,
                                                                                          ps.traffic)
                        if not satisfies:
                            v.append(PolicyViolation(tuple(lmbda), src_port, dst_port,  constraint, counter_example))

                    if constraint.constraint_type == ISOLATION_CONSTRAINT:
                        satisfies, counter_example = self.validate_isolation_constraint(src_port,
                                                                                        dst_port,
                                                                                        ps.traffic)

                        if not satisfies:
                            v.append(PolicyViolation(tuple(lmbda), src_port, dst_port,  constraint, counter_example))

                    if constraint.constraint_type == PATH_LENGTH_CONSTRAINT:
                        satisfies, counter_example = self.validate_path_length_constraint(src_port,
                                                                                          dst_port,
                                                                                          ps.traffic,
                                                                                          constraint.constraint_params)
                        if not satisfies:
                            v.append(PolicyViolation(tuple(lmbda), src_port, dst_port,  constraint, counter_example))

                    if constraint.constraint_type == LINK_AVOIDANCE_CONSTRAINT:
                        satisfies, counter_example = self.validate_link_avoidance(ps.src_zone,
                                                                                    ps.dst_zone,
                                                                                    ps.traffic,
                                                                                    constraint.constraint_params)

                        if not satisfies:
                            v.append(PolicyViolation(tuple(lmbda), src_port, dst_port,  constraint, counter_example))

        return v

    def truncate_recursion(self, v):

        for link_perm in list(self.validation_map.keys()):

            # For any k larger than len(lmbda) for this prefix of links.
            if len(link_perm) > len(v.lmbda):

                if tuple(v.lmbda) == tuple(link_perm[0:len(v.lmbda)]):

                    if (v.src_port, v.dst_port) in self.validation_map[link_perm]:

                        # This is indicated by removing those cases from the validation_map
                        ps_list = self.validation_map[link_perm][(v.src_port, v.dst_port)]
                        del self.validation_map[link_perm][(v.src_port, v.dst_port)]

                        print "Removed:", link_perm, "for src_port:", v.src_port, "dst_port:", v.dst_port

                        # If all the cases under a perm are gone, then get rid of the key.
                        if not self.validation_map[link_perm]:
                            print "Removed perm:", link_perm
                            del self.validation_map[link_perm]

                        v_p = PolicyViolation(tuple(link_perm), v.src_port, v.dst_port, v.constraint, v.counter_example)
                        self.violations.append(v_p)

    def perform_optimizations(self, v):

        for vio in v:

            if self.optimization_type == "No_Optimization":
                continue

            elif self.optimization_type == "DeterministicPermutation_PathCheck":
                    all_paths_ld = self.network_graph.get_all_paths_as_switch_link_data(vio.src_port.sw,
                                                                                        vio.dst_port.sw)
                    remaining_paths = all_paths_ld[:]
                    for ld in vio.lmbda:
                        for path in all_paths_ld:
                            if ld in path and path in remaining_paths:
                                remaining_paths.remove(path)

                    if not remaining_paths:
                        # Remove them for validation_map and add corresponding violations
                        self.truncate_recursion(vio)


    def perform_validation(self, lmbda):

        # Capture any changes to where the paths flow now
        self.initialize_per_link_traffic_paths()

        # Perform the validation that needs performing here...
        print "Performing validation, prefix here:", lmbda

        # Collect cases cases where lmbda == keys in the validation_map and validate them
        cases = {}
        for link_perm in self.validation_map:
            if link_perm == tuple(lmbda):
                cases.update(self.validation_map[link_perm])
        v = self.validate_policy_cases(cases, lmbda)
        self.violations.extend(v)

        self.perform_optimizations(v)

        # If max_k links have already been failed, no need to fail any more links
        if len(lmbda) < self.max_k:

            # Rotate through the links
            for link in self.L:
                # Select the link by checking that it is not in the lmbda already
                # Add the selected link to fail to the prefix
                if link in lmbda:
                    continue

                # If the permutation is not in validation_map, then no test it
                if tuple(lmbda + [link]) not in self.validation_map:
                    print "Truncated recursion tree for:", tuple(lmbda + [link])
                    continue

                # Fail the link
                print "Failing:", link
                self.port_graph.remove_node_graph_link(link.forward_link[0], link.forward_link[1])
                lmbda.append(link)

                # Recurse
                self.perform_validation(lmbda)

                # Restore the link
                print "Restoring:", link
                self.port_graph.add_node_graph_link(link.forward_link[0], link.forward_link[1], updating=True)
                lmbda.remove(link)

    def validate_policy(self, policy_statement_list, optimization_type="DeterministicPermutation_PathCheck"):

        self.optimization_type = optimization_type

        if self.optimization_type == "No_Optimization":
            self.L = list(self.network_graph.get_switch_link_data())
        elif self.optimization_type == "DeterministicPermutation_PathCheck":
            self.L = sorted(self.network_graph.get_switch_link_data(),
                            key=lambda ld: (ld.link_tuple[0], ld.link_tuple[1]))

        # Avoid duplication of effort across policies
        # validation_map is a two-dimensional dictionary:
        #   First key 'k-size' permutations, second key: (src_port, dst_port).
        #   Value is a list of statements where the pair appears

        self.validation_map = defaultdict(defaultdict)

        for ps in policy_statement_list:
            for i in range(ps.k+1):

                for link_perm in itertools.permutations(self.L, i):

                    for src_port, dst_port in self.port_pair_iter(ps.src_zone, ps.dst_zone):

                        if (src_port, dst_port) not in self.validation_map[link_perm]:
                            self.validation_map[link_perm][(src_port, dst_port)] = []

                        self.validation_map[link_perm][(src_port, dst_port)].append(ps)

        # Now the validation
        self.max_k = len(max(self.validation_map.keys(), key=lambda link_perm: len(link_perm)))
        lmbda = []
        self.violations = []
        self.perform_validation(lmbda)

        print len(self.violations)
        return self.violations
