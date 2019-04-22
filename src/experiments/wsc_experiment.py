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

    def flow_validator_get_time_to_failure(self, stub, num_iterations, link_failure_rate, flows):

        mcp = flow_validator_pb2.MonteCarloParams(num_iterations=num_iterations,
                                                  link_failure_rate=link_failure_rate,
                                                  flows=flows,
                                                  seed=42)

        ttf = stub.GetTimeToDisconnect(mcp)

        print "Mean TTF: ", ttf.mean
        print "SD TTF:", ttf.sd
        print "Time taken:", ttf.time_taken

    def trigger(self):
        channel = grpc.insecure_channel('localhost:50051')
        stub = flow_validator_pb2_grpc.FlowValidatorStub(channel)

        self.flow_validator_initialize(stub)

        policy_match = dict()
        policy_match["eth_type"] = 0x0800

        flows = [flow_validator_pb2.Flow(src_port=flow_validator_pb2.PolicyPort(switch_id="s1", port_num=1),
                                         dst_port=flow_validator_pb2.PolicyPort(switch_id="s4", port_num=1),
                                         policy_match=policy_match)]

        self.flow_validator_get_time_to_failure(stub, 1000, 1.0, flows)


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
                              synthesis_params={"apply_group_intents_immediately": True,
                                                "k": 1})

    exp = AdHocNet(nc)
    exp.trigger()


if __name__ == "__main__":
    main()

