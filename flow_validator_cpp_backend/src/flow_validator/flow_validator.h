#ifndef __FLOW_VALIDATOR_BACKEND_FLOW_VALIDATOR_H__
#define __FLOW_VALIDATOR_BACKEND_FLOW_VALIDATOR_H__

#include "proto/flow_validator.grpc.pb.h"

using flow_validator::FlowValidator;
using flow_validator::NetworkGraph;
using flow_validator::Policy;
using flow_validator::PolicyViolation;
using flow_validator::InitializeInfo;
using flow_validator::ValidatePolicyInfo;

using grpc::ServerContext;
using grpc::Status;

class FlowValidatorImpl final : public FlowValidator::Service {
 public:
    explicit FlowValidatorImpl(){
        mem = new int[100];
    }

    ~FlowValidatorImpl() {
        delete mem;
    }

    Status Initialize(ServerContext* , const NetworkGraph* , InitializeInfo* ) override;
    Status ValidatePolicy(ServerContext* , const Policy* , ValidatePolicyInfo* ) override;

 private:
    int * mem;
};


#endif