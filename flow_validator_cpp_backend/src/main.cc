#include <iostream>
#include <fstream>
#include <string>
#include <boost/algorithm/string.hpp>
#include <grpc/grpc.h>
#include <grpcpp/server.h>
#include <grpcpp/server_builder.h>
#include <grpcpp/server_context.h>
#include <grpcpp/security/server_credentials.h>
#include "flow_validator/flow_validator.h"

using namespace std;


using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerReader;
using grpc::ServerWriter;

#include "boost/graph/adjacency_list.hpp"
#include "boost/graph/graphviz.hpp"

using namespace boost;

/* define the graph type
      listS: selects the STL list container to store 
            the OutEdge list
      vecS: selects the STL vector container to store 
            the vertices
      directedS: selects directed edges
*/
typedef adjacency_list< listS, vecS, directedS > digraph;

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

