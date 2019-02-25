#include <iostream>
#include <fstream>
#include <string>
#include <grpc/grpc.h>
#include <grpcpp/server.h>
#include <grpcpp/server_builder.h>
#include <grpcpp/server_context.h>
#include <grpcpp/security/server_credentials.h>
#include "flow_validator/flow_validator.h"

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerReader;
using grpc::ServerWriter;

using namespace std;

void RunServer() {
      string server_address("0.0.0.0:50051");
      FlowValidatorImpl service;
      ServerBuilder builder;
      builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
      builder.RegisterService(&service);
      std::unique_ptr<Server> server(builder.BuildAndStart());

      //interval_map_example();

      cout << "Server listening on " << server_address << endl;
      server->Wait();
}

int main() {
    RunServer();
    return 0;
}

