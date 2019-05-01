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

    def flow_validator_initialize(self, stub):
        rpc_ng = self.prepare_rpc_network_graph()
        init_info = stub.Initialize(rpc_ng)

        if init_info.successful:
            print "Server said initialization was successful, time taken:", init_info.time_taken
        else:
            print "Server said initialization was not successful"

    def prepare_policy_statement_all_host_pair_connectivity(self):

        rpc_all_src_host_ports = [flow_validator_pb2.PolicyPort(switch_id="s1", port_num=1),
                                  flow_validator_pb2.PolicyPort(switch_id="s2", port_num=1),
                                  flow_validator_pb2.PolicyPort(switch_id="s3", port_num=1),
                                  flow_validator_pb2.PolicyPort(switch_id="s4", port_num=1)]

        rpc_all_dst_host_ports = rpc_all_src_host_ports

        # rpc_all_src_host_ports = [flow_validator_pb2.PolicyPort(switch_id="s4", port_num=1)]
        # rpc_all_dst_host_ports = [flow_validator_pb2.PolicyPort(switch_id="s2", port_num=1)]

        rpc_src_zone = flow_validator_pb2.Zone(ports=rpc_all_src_host_ports)
        rpc_dst_zone = flow_validator_pb2.Zone(ports=rpc_all_dst_host_ports)

        policy_match = dict()
        policy_match["eth_type"] = 0x0800

        rpc_constraints = [flow_validator_pb2.Constraint(type=CONNECTIVITY_CONSTRAINT)]

        rpc_lmbdas = [flow_validator_pb2.Lmbda(links=[self.rpc_links["s4"]["s1"], self.rpc_links["s4"]["s3"]])]

        rpc_policy_statement = flow_validator_pb2.PolicyStatement(src_zone=rpc_src_zone,
                                                                  dst_zone=rpc_dst_zone,
                                                                  policy_match=policy_match,
                                                                  constraints=rpc_constraints,
                                                                  lmbdas=rpc_lmbdas)

        return rpc_policy_statement

    def flow_validator_validate_policy(self, stub, rpc_policy_statements):

        rpc_p = flow_validator_pb2.Policy(policy_statements=rpc_policy_statements)

        validate_info = stub.ValidatePolicy(rpc_p)

        if validate_info.successful:
            print "Server said validation was successful, time taken:", validate_info.time_taken
        else:
            print "Server said validation was not successful"

        print "Total violations:", len(validate_info.violations)

        print validate_info.violations

    def __init__(self, network_graph):
        self.network_graph = network_graph
        self.port_graph = NetworkPortGraph(network_graph)

    def init_network_port_graph(self):
        self.port_graph.init_network_port_graph()
        self.port_graph.init_network_admitted_traffic()

    def de_init_network_port_graph(self):
        self.port_graph.de_init_network_port_graph()

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