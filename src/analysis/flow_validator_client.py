from __future__ import print_function

import grpc

from rpc import flow_validator_pb2
from rpc import flow_validator_pb2_grpc


def flow_validator_initialize(stub):
    port = flow_validator_pb2.Port(port_num=1, hw_addr="aa:bb")
    switch = flow_validator_pb2.Switch(ports=[port])
    network_graph = flow_validator_pb2.NetworkGraph(switches=[switch])

    status = stub.Initialize(network_graph)
    if status.init_successful == 1:
        print("Server said Init was successful")

    if status.init_successful == 2:
        print("Server said Init was not successful")


def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = flow_validator_pb2_grpc.FlowValidatorStub(channel)
    flow_validator_initialize(stub)


if __name__ == '__main__':
    run()
