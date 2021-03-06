# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

import flow_validator_pb2 as flow__validator__pb2


class FlowValidatorStub(object):
  # missing associated documentation comment in .proto file
  pass

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.Initialize = channel.unary_unary(
        '/flow_validator.FlowValidator/Initialize',
        request_serializer=flow__validator__pb2.NetworkGraph.SerializeToString,
        response_deserializer=flow__validator__pb2.InitializeInfo.FromString,
        )
    self.GetActiveFlowPath = channel.unary_unary(
        '/flow_validator.FlowValidator/GetActiveFlowPath',
        request_serializer=flow__validator__pb2.ActivePathParams.SerializeToString,
        response_deserializer=flow__validator__pb2.ActivePathInfo.FromString,
        )
    self.GetTimeToDisconnect = channel.unary_unary(
        '/flow_validator.FlowValidator/GetTimeToDisconnect',
        request_serializer=flow__validator__pb2.MonteCarloParams.SerializeToString,
        response_deserializer=flow__validator__pb2.TimeToDisconnectInfo.FromString,
        )
    self.GetNumActiveFlowsAtFailureTimes = channel.unary_unary(
        '/flow_validator.FlowValidator/GetNumActiveFlowsAtFailureTimes',
        request_serializer=flow__validator__pb2.NumActiveFlowsParams.SerializeToString,
        response_deserializer=flow__validator__pb2.NumActiveFlowsInfo.FromString,
        )


class FlowValidatorServicer(object):
  # missing associated documentation comment in .proto file
  pass

  def Initialize(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def GetActiveFlowPath(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def GetTimeToDisconnect(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def GetNumActiveFlowsAtFailureTimes(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_FlowValidatorServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'Initialize': grpc.unary_unary_rpc_method_handler(
          servicer.Initialize,
          request_deserializer=flow__validator__pb2.NetworkGraph.FromString,
          response_serializer=flow__validator__pb2.InitializeInfo.SerializeToString,
      ),
      'GetActiveFlowPath': grpc.unary_unary_rpc_method_handler(
          servicer.GetActiveFlowPath,
          request_deserializer=flow__validator__pb2.ActivePathParams.FromString,
          response_serializer=flow__validator__pb2.ActivePathInfo.SerializeToString,
      ),
      'GetTimeToDisconnect': grpc.unary_unary_rpc_method_handler(
          servicer.GetTimeToDisconnect,
          request_deserializer=flow__validator__pb2.MonteCarloParams.FromString,
          response_serializer=flow__validator__pb2.TimeToDisconnectInfo.SerializeToString,
      ),
      'GetNumActiveFlowsAtFailureTimes': grpc.unary_unary_rpc_method_handler(
          servicer.GetNumActiveFlowsAtFailureTimes,
          request_deserializer=flow__validator__pb2.NumActiveFlowsParams.FromString,
          response_serializer=flow__validator__pb2.NumActiveFlowsInfo.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'flow_validator.FlowValidator', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))
