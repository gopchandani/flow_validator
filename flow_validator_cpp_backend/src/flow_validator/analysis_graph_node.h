#ifndef __FLOW_VALIDATOR_BACKEND_ANALYSIS_GRAPH_NODE_H__
#define __FLOW_VALIDATOR_BACKEND_ANALYSIS_GRAPH_NODE_H__

#include <queue>
#include "rule.h"

using namespace std;


class AnalysisGraphNode final {
public:
    string node_id;
    uint64_t port_num;
    

    vector<Rule*> rules;

    AnalysisGraphNode(string, uint64_t);
    AnalysisGraphNode(string);

private:

};

#endif