#include <iostream>
#include <fstream>
#include <string>
#include <boost/algorithm/string.hpp>
#include <grpc/grpc.h>
#include <grpcpp/server.h>
#include <grpcpp/server_builder.h>
#include <grpcpp/server_context.h>
#include <grpcpp/security/server_credentials.h>
#include "proto/flow_validator.grpc.pb.h"

using namespace std;

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::ServerReader;
using grpc::ServerWriter;
using grpc::Status;

using flow_validator::FlowValidator;
using flow_validator::NetworkGraph;
using flow_validator::Policy;
using flow_validator::PolicyViolation;
using flow_validator::InitializeInfo;
using flow_validator::ValidatePolicyInfo;


class FlowValidatorImpl final : public FlowValidator::Service {
 public:
  explicit FlowValidatorImpl() {

  }

  Status Initialize(ServerContext* context, const NetworkGraph* ng, InitializeInfo* info) override {
    cout << "Received Initialize request" << endl;

    info->set_successful(true);
    info->set_time_taken(0.1);

    return Status::OK;
  }

  Status ValidatePolicy(ServerContext* context, const Policy* p, ValidatePolicyInfo* info) override {
    cout << "Received ValidatePolicy request" << endl;

    info->set_successful(true);
    info->set_time_taken(0.1);


    return Status::OK;
  }

 private:

};

void RunServer() {
  std::string server_address("0.0.0.0:50051");
  FlowValidatorImpl service;
  ServerBuilder builder;
  builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
  builder.RegisterService(&service);
  std::unique_ptr<Server> server(builder.BuildAndStart());
  std::cout << "Server listening on " << server_address << std::endl;
  server->Wait();
}

int main() {
    RunServer();
    return 0;
}

