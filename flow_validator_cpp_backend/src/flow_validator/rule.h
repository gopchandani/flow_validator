#ifndef __FLOW_VALIDATOR_BACKEND_RULE_H__
#define __FLOW_VALIDATOR_BACKEND_RULE_H__

#include "of_constants.h"
#include "proto/flow_validator.grpc.pb.h"
#include "rule_effect.h"
#include <unordered_map>
#include <tuple>

using namespace std;
using namespace flow_validator;

typedef std::unordered_map<string, std::tuple<int, int> > flow_rule_match_t;

class RuleEffect;

class Rule {
public:
    int priority;
    flow_rule_match_t flow_rule_match;
    vector<RuleEffect> rule_effects;

    Rule(int p) {
        priority = p;
    }

    flow_rule_match_t* get_resulting_flow_rule_match(flow_rule_match_t*);

};


#endif