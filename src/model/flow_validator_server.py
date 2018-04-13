from concurrent import futures
import time
import grpc

from rpc import flow_validator_pb2
from rpc import flow_validator_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


def get_network_graph_object(context):
    ng_obj = 1

    print(context)

    return ng_obj


class FlowValidatorServicer(flow_validator_pb2_grpc.FlowValidatorServicer):

    def __init__(self):
        pass

    def Initialize(self, request, context):
        ng_obj = get_network_graph_object(context)

        init_successful = 1

        return flow_validator_pb2.Status(init_successful=init_successful)


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