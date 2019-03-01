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

    RuleEffect(Instruction i) {
        if (i.type() == "APPLY_ACTIONS") {
            for (int k=0; k<i.actions_size(); k++)
            {
                cout << i.actions(k).type() << endl;
                if (i.actions(k).type() == "OUTPUT") {
                    cout << "Output Port: " << i.actions(k).output_port_num() << endl;

                    if (i.actions(k).output_port_num() == OUT_TO_IN_PORT) {
                        cout << "InPort" << endl;
                        bolt_back = true;
                    }

                } else 
                if (i.actions(k).type() == "GROUP") {
                    cout << "Group Id: " << i.actions(k).group_id() << endl;
                } else
                if (i.actions(k).type() == "PUSH_VLAN") {

                } else
                if (i.actions(k).type() == "SET_FIELD") {
                    cout << "Set Field: " << i.actions(k).modified_field() << endl;
                    cout << "Set Field Value: " << i.actions(k).modified_value() << endl;
                    packet_modifications[i.actions(k).modified_field()] =  i.actions(k).modified_value();
                } else
                if (i.actions(k).type() == "POP_VLAN") {

                } 
            }
        }
        //TODO
        else 
        if (i.type() == "WRITE_ACTIONS") {
        }
        else 
        if (i.type() == "GOTO_TABLE") {
        }
    }
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