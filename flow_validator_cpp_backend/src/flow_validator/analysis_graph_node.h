#ifndef __FLOW_VALIDATOR_BACKEND_ANALYSIS_GRAPH_NODE_H__
#define __FLOW_VALIDATOR_BACKEND_ANALYSIS_GRAPH_NODE_H__

#include <queue>
#include "rule.h"

using namespace std;

class LessThanByPriority
{
public:
    bool operator()(const Rule* lhs, const Rule* rhs) const
    {
        return lhs->priority < rhs->priority;
    }
};

class AnalysisGraphNode final {
public:
    string node_id;
    //std::priority_queue<Rule*, std::vector<Rule*>, LessThanByPriority> rules;

    vector<Rule*> rules;

    AnalysisGraphNode(string);

private:

};

#endif