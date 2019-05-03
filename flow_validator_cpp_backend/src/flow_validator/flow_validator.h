#ifndef __FLOW_VALIDATOR_BACKEND_FLOW_VALIDATOR_H__
#define __FLOW_VALIDATOR_BACKEND_FLOW_VALIDATOR_H__

#include "proto/flow_validator.grpc.pb.h"
#include "analysis_graph.h"
#include "thread_pool.h"

#include <iostream>
#include <fstream>
#include <string>
#include <numeric>

using namespace flow_validator;
using namespace std;

using grpc::ServerContext;
using grpc::Status;

class FlowValidatorImpl final : public FlowValidator::Service {
 public:
      explicit FlowValidatorImpl(){
          thread_pool = new ThreadPool(std::thread::hardware_concurrency());
          ag = NULL;
      }

      ~FlowValidatorImpl() {
      }

      Status Initialize(ServerContext*, const NetworkGraph*, InitializeInfo* ) override;
      Status GetActiveFlowPath(ServerContext*, const ActivePathParams*, ActivePathInfo*) override;
      Status GetTimeToDisconnect(ServerContext*, const MonteCarloParams*, TimeToDisconnectInfo* ) override;
      Status GetNumActiveFlowsAtFailureTimes(ServerContext*, const NumActiveFlowsParams*, NumActiveFlowsInfo*) override;

 private:
      ThreadPool *thread_pool;
      AnalysisGraph *ag;

};


#endif