#ifndef __SDNSIM_RULE_EFFECT_H__
#define __SDNSIM_RULE_EFFECT_H__

#include "common_types.h"
#include "of_constants.h"
#include "proto/sdnsim.grpc.pb.h"
#include <unordered_map>
#include <tuple>

using namespace std;
using namespace sdnsim;

class AnalysisGraph;
class AnalysisGraphNode;
class GroupEffect;

class RuleEffect {
public:
    // Things that happen once a rule matches:

    // -- Make direct modifications to the packet itself
    policy_match_t packet_modifications;

    // ---- Management of the action set
    // TODO
    // Add things to action set
    // Remove all things in the action set

    // ---- Apply the effects of going to a group
    GroupEffect *group_effect;

    // ---- Picking of the next node
    // Go to the node representing the next table or output port
    AnalysisGraphNode *next_node;

    // Go back to whatever port it came from
    bool bolt_back;

    RuleEffect();
    RuleEffect(AnalysisGraph *, Bucket, string); 
    RuleEffect(AnalysisGraph *, Instruction, string); 
    void get_modified_policy_match(policy_match_t*);

};

#endif