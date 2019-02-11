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

#include "boost/graph/adjacency_list.hpp"
#include "boost/graph/graphviz.hpp"

using namespace std;

using namespace boost;

/* define the graph type
      listS: selects the STL list container to store 
            the OutEdge list
      vecS: selects the STL vector container to store 
            the vertices
      directedS: selects directed edges
*/
typedef adjacency_list< listS, vecS, directedS > digraph;

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

  void adjacency_list_example() {


      // instantiate a digraph object with 8 vertices
      digraph g(8);

      // add some edges
      add_edge(0, 1, g);
      add_edge(1, 5, g);
      add_edge(5, 6, g);
      add_edge(2, 3, g);
      add_edge(2, 4, g);
      add_edge(3, 5, g);
      add_edge(4, 5, g);
      add_edge(5, 7, g);

      // represent graph in DOT format and send to cout
      write_graphviz(cout, g);

  }

  Status Initialize(ServerContext* context, const NetworkGraph* ng, InitializeInfo* info) override {
    cout << "Received Initialize request" << endl;

    info->set_successful(true);
    info->set_time_taken(0.1);

    adjacency_list_example();

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

