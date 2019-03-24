#ifndef __FLOW_VALIDATOR_BACKEND_RULE_EFFECT_H__
#define __FLOW_VALIDATOR_BACKEND_RULE_EFFECT_H__

#include "common_types.h"
#include "of_constants.h"
#include "proto/flow_validator.grpc.pb.h"
#include <unordered_map>
#include <tuple>

using namespace std;
using namespace flow_validator;

class AnalysisGraph;
class AnalysisGraphNode;

class RuleEffect {
public:
    // Things that happen once a rule matches:

    // -- Make direct modifications to the packet itself
    policy_match_t packet_modifications;

    // ---- Management of the action set
    // TODO
    // Add things to action set
    // Remove all things in the action set

    // ---- Picking of the next node
    // Goto the node representing the next table
    // Goto an output port (as the only option or as failover)
    AnalysisGraphNode *next_node;

    // Go back to whatever port it came from
    bool bolt_back;

    RuleEffect(); 
    RuleEffect(AnalysisGraph *, Instruction,  string); 

};

#endif