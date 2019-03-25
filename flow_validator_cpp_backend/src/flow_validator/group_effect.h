#ifndef __FLOW_VALIDATOR_BACKEND_GROUP_EFFECT_H__
#define __FLOW_VALIDATOR_BACKEND_GROUP_EFFECT_H__

#include "proto/flow_validator.grpc.pb.h"

using namespace flow_validator;
using namespace std;

class GroupEffect {
public:
    int32_t group_id;
    string group_type;
    string group_key;

    GroupEffect(Switch, Group);
};

#endif