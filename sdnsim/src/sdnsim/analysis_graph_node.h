#ifndef __SDNSIM_ANALYSIS_GRAPH_NODE_H__
#define __SDNSIM_ANALYSIS_GRAPH_NODE_H__

#include <queue>
#include "rule.h"

using namespace std;
using namespace sdnsim;

class AnalysisGraphNode final {
public:
    string node_id;
    vector<Rule*> rules;

    // Constructor and fields  for ports
    uint64_t port_num;
    AnalysisGraphNode *connected_host;
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