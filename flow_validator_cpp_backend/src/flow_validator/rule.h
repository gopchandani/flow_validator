#ifndef __FLOW_VALIDATOR_BACKEND_RULE_H__
#define __FLOW_VALIDATOR_BACKEND_RULE_H__

#include "of_constants.h"
#include "proto/flow_validator.grpc.pb.h"
#include "rule_effect.h"
#include <unordered_map>
#include <tuple>

using namespace std;
using namespace flow_validator;

typedef std::unordered_map<string, std::tuple<uint64_t, uint64_t> > flow_rule_match_t;
typedef std::unordered_map<string, uint64_t> policy_match_t;

class RuleEffect;

class Rule {
public:
    int priority;
    flow_rule_match_t flow_rule_match;
    vector<RuleEffect> rule_effects;

    Rule(int p) {
        priority = p;
    }

    policy_match_t* get_resulting_policy_match(policy_match_t*);

};


#endif