#ifndef __SDNSIM_SDNSIM_H__
#define __SDNSIM_SDNSIM_H__

#include "proto/sdnsim.grpc.pb.h"
#include "analysis_graph.h"
#include "thread_pool.h"

#include <iostream>
#include <fstream>
#include <string>
#include <numeric>

using namespace sdnsim;
using namespace std;

using grpc::ServerContext;
using grpc::Status;

class SDNSimImpl final : public SDNSim::Service {
 public:
      explicit SDNSimImpl(){
          thread_pool = new ThreadPool(std::thread::hardware_concurrency());
          ag = NULL;
      }

      ~SDNSimImpl() {
      }

      Status Initialize(ServerContext*, const NetworkGraph*, InitializeInfo* ) override;
      Status GetActiveFlowPath(ServerContext*, const ActivePathParams*, ActivePathInfo*) override;
      Status GetTimeToDisconnect(ServerContext*, const MonteCarloParams*, TimeToDisconnectInfo* ) override;
      Status GetNumActiveFlowsWhenLinksFail(ServerContext*, const NumActiveFlowsParams*, NumActiveFlowsInfo*) override;

 private:
      ThreadPool *thread_pool;
      AnalysisGraph *ag;
};


#endif