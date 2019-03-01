#ifndef __FLOW_VALIDATOR_BACKEND_ANALYSIS_GRAPH_NODE_H__
#define __FLOW_VALIDATOR_BACKEND_ANALYSIS_GRAPH_NODE_H__

#include <queue>
#include "rule.h"

using namespace std;

class AnalysisGraphNode final {
public:
    string node_id;
    std::priority_queue<Rule*, std::vector<Rule*>, LessThanByPriority> rules;

    AnalysisGraphNode(string);
    void interval_map_example();

private:

};

#endif