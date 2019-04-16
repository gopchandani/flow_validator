import sys
import grpc
from rpc import flow_validator_pb2
from rpc import flow_validator_pb2_grpc
from experiment import Experiment
from experiments.network_configuration import NetworkConfiguration
from analysis.policy_statement import CONNECTIVITY_CONSTRAINT

__author__ = 'Rakesh Kumar'

sys.path.append("./")


class AdHocNet(Experiment):

    def __init__(self, nc):

        super(AdHocNet, self).__init__("playground", 1)
        self.nc = nc
        self.rpc_links = self.init_rpc_links()

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

    def prepare_policy_statement_test_case(self):

        rpc_src_zone = flow_validator_pb2.Zone(ports=[flow_validator_pb2.PolicyPort(switch_id="s1", port_num=1)])
        rpc_dst_zone = flow_validator_pb2.Zone(ports=[flow_validator_pb2.PolicyPort(switch_id="s2", port_num=1)])

        policy_match = dict()
        policy_match["eth_type"] = 0x0800

        rpc_constraints = [flow_validator_pb2.Constraint(type=CONNECTIVITY_CONSTRAINT)]

        rpc_lmbdas = [flow_validator_pb2.Lmbda(links=[self.rpc_links["s2"]["s1"]])]

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

    def flow_validator_get_time_to_failure(self, stub, num_iterations, link_failure_rate, src_ports, dst_ports):

        mcp = flow_validator_pb2.MonteCarloParams(num_iterations=num_iterations,
                                                  link_failure_rate=link_failure_rate,
                                                  src_ports=src_ports,
                                                  dst_ports=dst_ports)

        ttf = stub.GetTimeToDisconnect(mcp)

        print "Mean TTF: ", ttf.mean
        print "SD TTF:", ttf.sd
        print "Time taken:", ttf.time_taken

    def trigger(self):
        #ng = self.nc.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

        channel = grpc.insecure_channel('localhost:50051')
        stub = flow_validator_pb2_grpc.FlowValidatorStub(channel)

        self.flow_validator_initialize(stub)

        rpc_policy_statement = self.prepare_policy_statement_all_host_pair_connectivity()

        #rpc_policy_statement = self.prepare_policy_statement_test_case()

        #self.flow_validator_validate_policy(stub, [rpc_policy_statement])

        src_ports = [flow_validator_pb2.PolicyPort(switch_id="s1", port_num=1)]
        dst_ports = [flow_validator_pb2.PolicyPort(switch_id="s4", port_num=1)]

        self.flow_validator_get_time_to_failure(stub, 10, 1.0, src_ports, dst_ports)


def main():
    nc = NetworkConfiguration("ryu",
                              "127.0.0.1",
                              6633,
                              "http://localhost:8080/",
                              "admin",
                              "admin",
                              "adhoc",
                              {"num_switches": 4,
                               "seed": 42,
                               "num_hosts_per_switch": 1,
                               "min_x": -100,
                               "max_x":  100,
                               "min_y": -100,
                               "max_y":  100
                               },
                              conf_root="configurations/",
                              synthesis_name="DijkstraSynthesis",
                              #synthesis_name="AboresceneSynthesis",
                              synthesis_params={"apply_group_intents_immediately": True,
                                                "k": 1})

    exp = AdHocNet(nc)
    exp.trigger()


if __name__ == "__main__":
    main()

