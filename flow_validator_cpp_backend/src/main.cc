#include <iostream>
#include <fstream>
#include <string>
#include <grpc/grpc.h>
#include <grpcpp/server.h>
#include <grpcpp/server_builder.h>
#include <grpcpp/server_context.h>
#include <grpcpp/security/server_credentials.h>
#include "flow_validator/flow_validator.h"
#include <set>

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerReader;
using grpc::ServerWriter;

#include <boost/algorithm/string.hpp>
#include "boost/icl/interval_map.hpp"
#include "boost/icl/interval.hpp"

typedef std::set<string> ids;

using namespace std;

void interval_map_example() {

      ids ids1;   
      ids1.insert("T1");
      ids ids2;
      ids2.insert("T2");
      
      boost::icl::interval_map<int, ids> mymap;
      auto i1 = boost::icl::interval<int>::closed(2, 7);
      auto i2 = boost::icl::interval<int>::closed(3, 8);
      mymap += make_pair(i1, ids1);
      mymap += make_pair(i2, ids2);
      
      cout << mymap << endl;

}

void RunServer() {
      string server_address("0.0.0.0:50051");
      FlowValidatorImpl service;
      ServerBuilder builder;
      builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
      builder.RegisterService(&service);
      std::unique_ptr<Server> server(builder.BuildAndStart());

      //interval_map_example();

      std::cout << "Server listening on " << server_address << std::endl;
      server->Wait();
}

int main() {
    RunServer();
    return 0;
}

