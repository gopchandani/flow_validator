#ifndef __FLOW_VALIDATOR_BACKEND_RULE_H__
#define __FLOW_VALIDATOR_BACKEND_RULE_H__

#include "of_constants.h"
#include "proto/flow_validator.grpc.pb.h"
#include <unordered_map>
#include <tuple>

using namespace std;
using namespace flow_validator;


class RuleEffect {
public:
    // Things that happen once a rule matches:

    // -- Make direct modifications to the packet itself
    std::unordered_map<string, int> packet_modifications;

    // ---- Management of the action set
    // TODO
    // Add things to action set
    // Remove all things in the action set

    // ---- Picking of the next node
    // Goto the node representing the next table
    // Goto an output port (as the only option or as failover)
    //AnalysisGraphNode *next_node;

    // Go back to whatever port it came from
    bool bolt_back;

    RuleEffect(Instruction); 
};


class Rule {
public:
    int priority;
    std::unordered_map<string, std::tuple<int, int> > flow_rule_match;
    vector<RuleEffect> rule_effects;

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