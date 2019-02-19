#ifndef __FLOW_VALIDATOR_BACKEND_FLOW_VALIDATOR_H__
#define __FLOW_VALIDATOR_BACKEND_FLOW_VALIDATOR_H__

#include "proto/flow_validator.grpc.pb.h"

#include <iostream>
#include <fstream>
#include <string>

using namespace flow_validator;
using namespace std;

using grpc::ServerContext;
using grpc::Status;

class FlowValidatorImpl final : public FlowValidator::Service {
 public:
    explicit FlowValidatorImpl(){
    }

    ~FlowValidatorImpl() {
    }

    Status Initialize(ServerContext* , const NetworkGraph* , InitializeInfo* ) override;
    Status ValidatePolicy(ServerContext* , const Policy* , ValidatePolicyInfo* ) override;

 private:
};


#endif