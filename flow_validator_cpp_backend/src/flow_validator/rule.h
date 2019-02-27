#ifndef __FLOW_VALIDATOR_BACKEND_RULE_H__
#define __FLOW_VALIDATOR_BACKEND_RULE_H__

#include "proto/flow_validator.grpc.pb.h"

#include <unordered_map>
#include <tuple>

using namespace std;
using namespace flow_validator;


class RuleEffect {
public:
    bool applies_immediately;

    // Things that happen once a rule matches:

    // 1. Goto another table node
    // 2. Goto an output port (as the only option or as failover)
    // 3. Go back to whatever port it came from
    // 3. Modify the map that the search is carrying around immediately before going to the next node
    // 4. Accumulate modifications to the map for being applied at the last node before exiting the switch
};


class Rule {
public:
    int priority;
    std::unordered_map<string, std::tuple<int, int> > flow_rule_match;

    Rule(int p) {
        priority = p;
    }
};

class LessThanByPriority
{
public:
    bool operator()(const Rule* lhs, const Rule* rhs) const
    {
        return lhs->priority < rhs->priority;
    }
};

#endif