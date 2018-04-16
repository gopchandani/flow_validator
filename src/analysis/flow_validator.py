import sys
import time
import grpc

sys.path.append("./")

from collections import defaultdict
from experiments.timer import Timer
from model.network_port_graph import NetworkPortGraph
from model.traffic import Traffic
from util import get_specific_traffic
from util import get_admitted_traffic, get_active_path, get_failover_path_after_failed_sequence
from analysis.policy_statement import CONNECTIVITY_CONSTRAINT, ISOLATION_CONSTRAINT
from analysis.policy_statement import PATH_LENGTH_CONSTRAINT, LINK_AVOIDANCE_CONSTRAINT
from analysis.policy_statement import PolicyViolation, PolicyStatement, PolicyConstraint

from model.network_graph import NetworkGraph
from concurrent import futures
from rpc import flow_validator_pb2
from rpc import flow_validator_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

__author__ = 'Rakesh Kumar'


class FlowValidator(object):

    def __init__(self, network_graph, report_active_state=False):
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

                path = get_active_path(self.port_graph,
                                       specific_traffic,
                                       src_host_obj.switch_port,
                                       dst_host_obj.switch_port)

                if path:

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
                traffic_path = get_active_path(self.port_graph, traffic, src_port, dst_port)

                if traffic_path:
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
                traffic_path = get_active_path(self.port_graph, traffic, src_port, dst_port)

                if traffic_path:
                    satisfies = False
                    counter_example = at

        return satisfies, counter_example

    def validate_path_length_constraint(self, src_port, dst_port, traffic, l):

        satisfies = True
        counter_example = None

        traffic_path = get_active_path(self.port_graph, traffic, src_port, dst_port)

        if traffic_path:
            if len(traffic_path) > l:
                satisfies = False
                counter_example = traffic_path

        return satisfies, counter_example

    def validate_link_avoidance(self, src_port, dst_port, traffic, el):
        satisfies = True
        counter_example = None

        active_path = get_active_path(self.port_graph, traffic, src_port, dst_port)

        # There needs to be a path to violate a link...
        if active_path:
            for ld in el:
                if active_path.passes_link(ld):
                    satisfies = False
                    counter_example = active_path
                    break

        return satisfies, counter_example

    def validate_port_pair_constraints(self, lmbda):

        # Capture any changes to where the paths flow now
        self.initialize_per_link_traffic_paths()

        print "Performing validation, lmbda:", lmbda

        v = []

        for src_port, dst_port in self.p_map[tuple(lmbda)]:

            for ps in self.p_map[tuple(lmbda)][(src_port, dst_port)]:

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
                        satisfies, counter_example = self.validate_link_avoidance(src_port,
                                                                                  dst_port,
                                                                                  ps.traffic,
                                                                                  constraint.constraint_params)

                        if not satisfies:
                            v.append(PolicyViolation(tuple(lmbda), src_port, dst_port,  constraint, counter_example))

        self.violations.extend(v)
        return v

    def validate_policy_without_preemption(self, lmbda):

        # Perform the validation that needs performing here...
        self.validate_port_pair_constraints(lmbda)

        # If max_k links have already been failed, no need to fail any more links
        if len(lmbda) < self.max_k:

            # Rotate through the links
            for next_link_to_fail in self.network_graph.L:
                # Select the link by checking that it is not in the lmbda already
                # Add the selected link to fail to the prefix
                if next_link_to_fail in lmbda:
                    continue

                # After checking for preemption, if the permutation is not in p_map, then no need to test it
                if tuple(lmbda + [next_link_to_fail]) not in self.p_map:
                    print "Truncated recursion tree for:", tuple(lmbda + [next_link_to_fail])
                    continue

                # Fail the link
                #print "Failing:", next_link_to_fail
                self.port_graph.remove_node_graph_link(next_link_to_fail.forward_link[0],
                                                       next_link_to_fail.forward_link[1])
                lmbda.append(next_link_to_fail)

                # Recurse
                self.validate_policy_without_preemption(lmbda)

                # Restore the link
                #print "Restoring:", next_link_to_fail
                self.port_graph.add_node_graph_link(next_link_to_fail.forward_link[0],
                                                    next_link_to_fail.forward_link[1],
                                                    updating=True)
                lmbda.remove(next_link_to_fail)

    def validate_policy_with_preemption(self, active_path_computation_times, path_lengths):

        for lmbda in self.p_map:
            for src_port, dst_port in list(self.p_map[lmbda].keys()):
                for ps in self.p_map[lmbda][(src_port, dst_port)]:

                    ps.traffic.set_field("ethernet_source",
                                         int(src_port.attached_host.mac_addr.replace(":", ""), 16))
                    ps.traffic.set_field("ethernet_destination",
                                         int(dst_port.attached_host.mac_addr.replace(":", ""), 16))
                    ps.traffic.set_field("in_port",
                                         int(src_port.port_number))

                    with Timer(verbose=True) as t:
                        active_path = get_active_path(self.port_graph, ps.traffic, src_port, dst_port)

                    if active_path_computation_times != None:
                        active_path_computation_times.append(t.secs)

                    if path_lengths != None:
                        path_lengths.append(len(active_path))

                    failover_path = None

                    if active_path:
                        failover_path = get_failover_path_after_failed_sequence(self.port_graph, active_path, lmbda)
                        
                    for constraint in ps.constraints:
                        if constraint.constraint_type == CONNECTIVITY_CONSTRAINT:
                            if not failover_path:
                                v = PolicyViolation(lmbda,
                                                    src_port,
                                                    dst_port,
                                                    constraint,
                                                    "")
                                self.violations.append(v)

                        elif constraint.constraint_type == LINK_AVOIDANCE_CONSTRAINT:
                            if failover_path:
                                passes_links = False

                                for ld in constraint.constraint_params:
                                    if failover_path.passes_link(ld):
                                        passes_links = True
                                        break

                                if passes_links:
                                    v = PolicyViolation(lmbda,
                                                        src_port,
                                                        dst_port,
                                                        constraint,
                                                        str(failover_path))
                                    self.violations.append(v)

                        elif constraint.constraint_type == PATH_LENGTH_CONSTRAINT:
                            if failover_path:
                                if len(failover_path) > constraint.constraint_params:
                                    v = PolicyViolation(lmbda,
                                                        src_port,
                                                        dst_port,
                                                        constraint,
                                                        str(failover_path))
                                    self.violations.append(v)

                        elif constraint.constraint_type == ISOLATION_CONSTRAINT:
                            if failover_path:
                                v = PolicyViolation(lmbda,
                                                    src_port,
                                                    dst_port,
                                                    constraint,
                                                    "")
                                self.violations.append(v)

    def validate_policy(self, policy_statement_list, optimization_type,
                        active_path_computation_times=None,
                        path_lengths=None):

        # Avoid duplication of effort across policies
        # p_map is a two-dimensional dictionary:
        #   First key permutation of link failures, second key: (src_port, dst_port).
        #   Value is a list of statements where the pair appears
        self.p_map = defaultdict(defaultdict)

        for ps in policy_statement_list:
            for lmbda in ps.lmbdas:
                for src_port, dst_port in self.port_pair_iter(ps.src_zone, ps.dst_zone):
                    if (src_port, dst_port) not in self.p_map[lmbda]:
                        self.p_map[lmbda][(src_port, dst_port)] = []
                    self.p_map[lmbda][(src_port, dst_port)].append(ps)

        # Now the validation
        self.max_k = len(max(self.p_map.keys(), key=lambda link_perm: len(link_perm)))
        self.violations = []

        if optimization_type == "With Preemption":
            self.validate_policy_with_preemption(active_path_computation_times, path_lengths)
        elif optimization_type == "Without Preemption":
            self.validate_policy_without_preemption([])

        return self.violations


class FlowValidatorServicer(flow_validator_pb2_grpc.FlowValidatorServicer):

    def __init__(self):
        self.fv = None
        self.ng_obj = None

    def get_network_graph_object(self, request):
        ng_obj = NetworkGraph(request.controller)
        ng_obj.parse_network_graph(request.switches, (request.hosts, request.links), request.links)
        return ng_obj

    def Initialize(self, request, context):
        self.ng_obj = self.get_network_graph_object(request)

        self.fv = FlowValidator(self.ng_obj)
        self.fv.init_network_port_graph()

        init_successful = 1

        return flow_validator_pb2.Status(init_successful=init_successful)

    def ValidatePolicy(self, request, context):

        src_zone = [self.ng_obj.get_node_object(h_id).switch_port for h_id in self.ng_obj.host_ids]
        dst_zone = [self.ng_obj.get_node_object(h_id).switch_port for h_id in self.ng_obj.host_ids]

        specific_traffic = Traffic(init_wildcard=True)
        specific_traffic.set_field("ethernet_type", 0x0800)

        constraints = [PolicyConstraint(CONNECTIVITY_CONSTRAINT, None)]

        s = PolicyStatement(self.ng_obj,
                            src_zone,
                            dst_zone,
                            specific_traffic,
                            constraints,
                            lmbdas=[tuple(self.ng_obj.get_switch_link_data(sw=self.ng_obj.get_node_object("s4")))])

        violations = self.fv.validate_policy([s], optimization_type="With Preemption")

        # Generate and return policy PolicyViolations
        policy_violations = []
        for v in violations:
            policy_violations.append(flow_validator_pb2.PolicyViolation())

        return flow_validator_pb2.PolicyViolations(violations=policy_violations)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    flow_validator_pb2_grpc.add_FlowValidatorServicer_to_server(
        FlowValidatorServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
