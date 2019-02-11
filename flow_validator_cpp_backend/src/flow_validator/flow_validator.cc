
#include <iostream>
#include <fstream>
#include <string>

using namespace std;

#include "flow_validator.h"


Status FlowValidatorImpl::Initialize(ServerContext* context, const NetworkGraph* ng, InitializeInfo* info) {
    cout << "Received Initialize request" << endl;

    info->set_successful(true);
    info->set_time_taken(0.1);

    return Status::OK;
}

Status FlowValidatorImpl::ValidatePolicy(ServerContext* context, const Policy* p, ValidatePolicyInfo* info) {
    cout << "Received ValidatePolicy request" << endl;

    info->set_successful(true);
    info->set_time_taken(0.1);


    return Status::OK;
}
