#ifndef __SDNSIM_RULE_H__
#define __SDNSIM_RULE_H__

#include "of_constants.h"
#include "proto/sdnsim.grpc.pb.h"
#include "rule_effect.h"
#include "common_types.h"

using namespace std;
using namespace sdnsim;

class RuleEffect;

class Rule {
public:
    int priority;
    flow_rule_match_t flow_rule_match;
    vector<RuleEffect*> rule_effects;

    Rule(int p) {
        priority = p;
    }

    policy_match_t* get_resulting_policy_match(policy_match_t*);

};


#endif