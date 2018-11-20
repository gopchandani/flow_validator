import sys
import time
import grpc

sys.path.append("./")

from collections import defaultdict
from experiments.timer import Timer
from model.network_port_graph import NetworkPortGraph
from model.traffic import Traffic
from model.traffic_element import TrafficElement
from model.match import Match
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

    def __init__(self, network_graph):
        self.network_graph = network_graph
        self.port_graph = NetworkPortGraph(network_graph)

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
                ps.traffic.set_field("has_vlan_tag", 0)

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

    def validate_policy(self, policy_statement_list, active_path_computation_times=None, path_lengths=None):

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

        for lmbda in self.p_map:
            for src_port, dst_port in list(self.p_map[lmbda].keys()):
                for ps in self.p_map[lmbda][(src_port, dst_port)]:

                    ps.traffic.set_field("ethernet_source",
                                         int(src_port.attached_host.mac_addr.replace(":", ""), 16))
                    ps.traffic.set_field("ethernet_destination",
                                         int(dst_port.attached_host.mac_addr.replace(":", ""), 16))
                    ps.traffic.set_field("in_port",
                                         int(src_port.port_number))
                    ps.traffic.set_field("has_vlan_tag", 0)

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

        return self.violations


class FlowValidatorServicer(flow_validator_pb2_grpc.FlowValidatorServicer):

    def __init__(self):
        self.fv = None
        self.ng_obj = None

    def get_network_graph_object(self, request):
        ng_obj = NetworkGraph(request.controller)
        ng_obj.parse_network_graph(request.switches, (request.hosts, request.links), request.links)
        return ng_obj

    def get_zone(self, zone_grpc):
        zone = []
        for port_grpc in zone_grpc.ports:
            host_sw_obj = self.ng_obj.get_node_object(port_grpc.switch_id)
            zone.append(host_sw_obj.ports[port_grpc.port_num])

        return zone

    def get_traffic(self, traffic_match_grpc):
        tm = Match(match_raw=traffic_match_grpc, controller="grpc", flow=self)
        te = TrafficElement(init_match=tm)
        t = Traffic()
        t.add_traffic_elements([te])
        return t

    def get_constraints(self, constraints_grpc):

        c = []
        for constraint_grpc in constraints_grpc:

            if constraint_grpc.type == CONNECTIVITY_CONSTRAINT:
                pc = PolicyConstraint(CONNECTIVITY_CONSTRAINT, None)
            elif constraint_grpc.type == ISOLATION_CONSTRAINT:
                pc = PolicyConstraint(ISOLATION_CONSTRAINT, None)
            elif constraint_grpc.type == PATH_LENGTH_CONSTRAINT:
                pc = PolicyConstraint(PATH_LENGTH_CONSTRAINT, constraint_grpc.path_length)
            elif constraint_grpc.type == LINK_AVOIDANCE_CONSTRAINT:
                pc = PolicyConstraint(LINK_AVOIDANCE_CONSTRAINT, constraint_grpc.avoid_links)

            c.append(pc)

        return c

    def get_lmbdas(self, lmbdas_grpc):
        lmbdas = []

        for lmbda_grpc in lmbdas_grpc:
            lmbda = []
            for link_grpc in lmbda_grpc.links:
                lmbda.append(self.ng_obj.get_link_data(link_grpc.src_node, link_grpc.dst_node))

            lmbdas.append(tuple(lmbda))

        return lmbdas

    def get_violations_grpc(self, violations):

        # Generate and return policy PolicyViolations
        violations_grpc = []
        for v in violations:

            grpc_lmbda_links = []
            for ld in v.lmbda:
                grpc_lmbda_links.append(flow_validator_pb2.PolicyLink(src_node=ld.node1_id, dst_node=ld.node2_id))

            grpc_lmbda = flow_validator_pb2.Lmbda(links=grpc_lmbda_links)
            grpc_src_port = flow_validator_pb2.PolicyPort(switch_id=v.src_port.sw.node_id,
                                                          port_num=v.src_port.port_number)

            grpc_dst_port = flow_validator_pb2.PolicyPort(switch_id=v.dst_port.sw.node_id,
                                                          port_num=v.dst_port.port_number)

            grpc_constraint_type = v.constraint.constraint_type
            grpc_counter_example = str(v.counter_example)

            violations_grpc.append(flow_validator_pb2.PolicyViolation(lmbda=grpc_lmbda,
                                                                      src_port=grpc_src_port,
                                                                      dst_port=grpc_dst_port,
                                                                      constraint_type=grpc_constraint_type,
                                                                      counter_example=grpc_counter_example))

        return flow_validator_pb2.PolicyViolations(violations=violations_grpc)

    def Initialize(self, request, context):
        self.ng_obj = self.get_network_graph_object(request)

        self.fv = FlowValidator(self.ng_obj)
        self.fv.init_network_port_graph()

        init_successful = 1

        return flow_validator_pb2.Status(init_successful=init_successful)

    def ValidatePolicy(self, request, context):

        policy = []
        for policy_statement in request.policy_statements:

            src_zone = self.get_zone(policy_statement.src_zone)
            dst_zone = self.get_zone(policy_statement.dst_zone)
            t = self.get_traffic(policy_statement.traffic_match)
            c = self.get_constraints(policy_statement.constraints)
            l = self.get_lmbdas(policy_statement.lmbdas)

            s = PolicyStatement(self.ng_obj, src_zone, dst_zone, t, c, l)
            policy.append(s)

        violations = self.fv.validate_policy(policy)

        return self.get_violations_grpc(violations)


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
