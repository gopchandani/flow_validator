#ifndef __FLOW_VALIDATOR_BACKEND_ANALYSIS_GRAPH_NODE_H__
#define __FLOW_VALIDATOR_BACKEND_ANALYSIS_GRAPH_NODE_H__

#include <queue>
#include "rule.h"

using namespace std;
using namespace flow_validator;

class AnalysisGraphNode final {
public:
    string node_id;
    vector<Rule*> rules;

    // Constructor and fields  for ports
    uint64_t port_num;
    AnalysisGraphNode *connected_host;
    bool is_live;
    AnalysisGraphNode(string, uint64_t);

    // Constructor and fields  for tables
    AnalysisGraphNode(string);

    // Constructor and fields for hosts
    string host_ip;
    string host_mac;
    AnalysisGraphNode(string, string, string);
private:

};

#endif