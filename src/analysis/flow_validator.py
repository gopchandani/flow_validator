import sys
import time
import grpc

sys.path.append("./")

from sdnsim_client import SDNSimClient
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


_ONE_DAY_IN_SECONDS = 60 * 60 * 24

__author__ = 'Rakesh Kumar'


class FlowValidator(object):

    def __init__(self, network_graph, use_sdnsim=False, nc=None):

        self.network_graph = network_graph
        self.use_sdnsim = use_sdnsim

        self.sdnsim_client = None
        self.port_graph = None

        if self.use_sdnsim:
            self.sdnsim_client = SDNSimClient(nc)
            self.sdnsim_client.initialize_sdnsim()
        else:
            self.port_graph = NetworkPortGraph(network_graph)
            self.init_network_port_graph()

    def init_network_port_graph(self):
        self.port_graph.init_network_port_graph()
        self.port_graph.init_network_admitted_traffic()

    def de_init_network_port_graph(self):
        self.port_graph.de_init_network_port_graph()

    def get_active_path(self, traffic, src_port, dst_port):

        traffic_path = None

        if self.use_sdnsim:
            traffic_path = self.sdnsim_client.get_active_flow_path(src_port.sw.node_id, src_port.port_number,
                                                                   dst_port.sw.node_id, dst_port.port_number,
                                                                   traffic,
                                                                   [])
        else:
            traffic.set_field("ethernet_source", int(src_port.attached_host.mac_addr.replace(":", ""), 16))
            traffic.set_field("ethernet_destination", int(dst_port.attached_host.mac_addr.replace(":", ""), 16))
            traffic.set_field("in_port", int(src_port.port_number))
            traffic.set_field("has_vlan_tag", 0)
            traffic_path = get_active_path(self.port_graph, traffic, src_port, dst_port)

        return traffic_path

    def passes_link(self, failover_path, ld):
        passes_link = False

        if self.use_sdnsim:
            for i in xrange(len(failover_path)-1):
                p1 = failover_path[i].split(":")[0]
                p2 = failover_path[i+1].split(":")[0]

                if ((p1 == ld.forward_link[0] and p2 == ld.forward_link[1])
                        or (p1 == ld.forward_link[1] and p2 == ld.forward_link[0])):
                    passes_link = True
                    break

        else:
            if failover_path.passes_link(ld):
                passes_link = True

        return passes_link

    def get_failover_path_after_failed_sequence(self, traffic, src_port, dst_port, active_path, lmbda):

        traffic_path = None

        if self.use_sdnsim:

            lmbda_list = []
            for l in lmbda:
                lmbda_list.append(l.forward_link)

            traffic_path = self.sdnsim_client.get_active_flow_path(src_port.sw.node_id, src_port.port_number,
                                                                   dst_port.sw.node_id, dst_port.port_number,
                                                                   traffic,
                                                                   lmbda_list)
        else:
            traffic_path = get_failover_path_after_failed_sequence(self.port_graph, active_path, lmbda)

        return traffic_path

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

                    with Timer(verbose=True) as t:
                        active_path = self.get_active_path(ps.traffic, src_port, dst_port)

                    if active_path_computation_times != None:
                        active_path_computation_times.append(t.secs)

                    if path_lengths != None:
                        path_lengths.append(len(active_path))

                    failover_path = None

                    if active_path:
                        failover_path = self.get_failover_path_after_failed_sequence(ps.traffic,
                                                                                     src_port,
                                                                                     dst_port,
                                                                                     active_path,
                                                                                     lmbda)

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
                                    if self.passes_link(failover_path, ld):
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