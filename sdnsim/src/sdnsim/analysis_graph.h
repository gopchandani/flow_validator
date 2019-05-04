#ifndef __FLOW_VALIDATOR_BACKEND_ANALYSIS_GRAPH_H__
#define __FLOW_VALIDATOR_BACKEND_ANALYSIS_GRAPH_H__

#include "proto/flow_validator.grpc.pb.h"

#include "common_types.h"
#include "of_constants.h"
#include "rule.h"

using namespace std;
using namespace flow_validator;

class AnalysisGraphNode;
class GroupEffect;

class AnalysisGraph final {
 public:
     AnalysisGraph(const NetworkGraph* ng);
     ~AnalysisGraph();
     void print_path(string, string, vector<string> & );
     bool path_has_loop(string, vector<string> &);
     bool is_node_inactive(string, Lmbda);

     uint64_t convert_mac_str_to_uint64(string);

     void init_adjacent_port_id_map(const NetworkGraph* ng);
     void add_wildcard_rule(AnalysisGraphNode *, AnalysisGraphNode *);
     void init_flow_table_rules(AnalysisGraphNode *, FlowTable, string);
     void init_graph_node_per_host(Host);
     void init_wildcard_rules_per_switch(Switch);
     void init_graph_nodes_per_switch(Switch);
     void init_group_table_per_switch(Switch);
     void init_flow_tables_per_switch(Switch);

     void apply_rule_effect(AnalysisGraphNode*, AnalysisGraphNode*, AnalysisGraphNode*, policy_match_t*, RuleEffect*, vector<vector<string> > &, vector<string> &, Lmbda);
     void find_packet_paths(AnalysisGraphNode*, AnalysisGraphNode*, AnalysisGraphNode*, policy_match_t*, vector<vector<string> > &, vector<string> &, Lmbda);
     vector<string> find_path(string, string, policy_match_t, Lmbda);
     double find_time_to_disconnect(const MonteCarloParams*, int);
     NumActiveFlowsRep get_num_active_flows(int, vector<Flow>, const NumActiveFlowsParams*);

    
     int total_flow_table_rules;
     vector<Link> all_switch_links;

     std::unordered_map<string, GroupEffect*> group_effects;
     std::unordered_map<string, string> adjacent_port_id_map;
     std::unordered_map<string, AnalysisGraphNode*> node_id_to_node_map;

 private:

};


#endif