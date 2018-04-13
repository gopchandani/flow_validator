import sys
import grpc
from rpc import flow_validator_pb2
from rpc import flow_validator_pb2_grpc
from experiment import Experiment
from experiments.network_configuration import NetworkConfiguration
from model.traffic import Traffic
from analysis.policy_statement import PolicyStatement, PolicyConstraint
from analysis.policy_statement import CONNECTIVITY_CONSTRAINT

__author__ = 'Rakesh Kumar'

sys.path.append("./")


class Playground2(Experiment):

    def __init__(self, nc):

        super(Playground2, self).__init__("playground", 1)
        self.nc = nc
        ng = self.nc.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

    def prepare_rpc_network_graph(self):

        switches = self.nc.get_switches()
        hosts = self.nc.get_host_nodes()
        links = self.nc.get_links()

        port = flow_validator_pb2.Port(port_num=1, hw_addr="aa:bb")
        switch = flow_validator_pb2.Switch(ports=[port])
        rpc_ng = flow_validator_pb2.NetworkGraph(switches=[switch], hosts=[], links=[])

        return rpc_ng

    def flow_validator_initialize(self, stub):
        rpc_ng = self.prepare_rpc_network_graph()
        status = stub.Initialize(rpc_ng)

        if status.init_successful == 1:
            print("Server said Init was successful")

        if status.init_successful == 2:
            print("Server said Init was not successful")

    def trigger(self):

        channel = grpc.insecure_channel('localhost:50051')
        stub = flow_validator_pb2_grpc.FlowValidatorStub(channel)
        self.flow_validator_initialize(stub)

        src_zone = [self.nc.ng.get_node_object(h_id).switch_port for h_id in self.nc.ng.host_ids]
        dst_zone = [self.nc.ng.get_node_object(h_id).switch_port for h_id in self.nc.ng.host_ids]

        specific_traffic = Traffic(init_wildcard=True)
        specific_traffic.set_field("ethernet_type", 0x0800)

        constraints = [PolicyConstraint(CONNECTIVITY_CONSTRAINT, None)]

        s = PolicyStatement(self.nc.ng,
                            src_zone,
                            dst_zone,
                            specific_traffic,
                            constraints,
                            lmbdas=[tuple(ng.get_switch_link_data(sw=ng.get_node_object("s4")))])

        # violations = fv.validate_policy([s], optimization_type="With Preemption")
        #
        # for v in violations:
        #     print v
        #
        # print "Done..."


def main():
    nc = NetworkConfiguration("ryu",
                              "127.0.0.1",
                              6633,
                              "http://localhost:8080/",
                              "admin",
                              "admin",
                              "cliquetopo",
                              {"num_switches": 4,
                               "num_hosts_per_switch": 1,
                               "per_switch_links": 2},
                              conf_root="configurations/",
                              synthesis_name="AboresceneSynthesis",
                              synthesis_params={"apply_group_intents_immediately": True})

    exp = Playground2(nc)
    exp.trigger()


if __name__ == "__main__":
    main()
