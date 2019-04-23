#ifndef __FLOW_VALIDATOR_BACKEND_ANALYSIS_GRAPH_H__
#define __FLOW_VALIDATOR_BACKEND_ANALYSIS_GRAPH_H__

#include "boost/graph/adjacency_list.hpp"
#include "boost/graph/graphviz.hpp"
#include "proto/flow_validator.grpc.pb.h"

#include "common_types.h"
#include "of_constants.h"
#include "rule.h"

using namespace boost;
using namespace std;
using namespace flow_validator;

typedef adjacency_list< vecS, vecS, directedS> analysis_graph;
typedef graph_traits<analysis_graph>::vertex_descriptor Vertex;
typedef graph_traits<analysis_graph>::edge_descriptor Edge;
typedef graph_traits<analysis_graph>::vertex_iterator vertex_iter;
typedef graph_traits<analysis_graph>::edge_iterator edge_iter;
typedef graph_traits<analysis_graph>::adjacency_iterator AdjacencyIterator;
typedef iterator_property_map<vector<default_color_type>::iterator, property_map<analysis_graph, vertex_index_t>::type > PathFinderColorMap;

class AnalysisGraphNode;
class GroupEffect;

class AnalysisGraph final {
 public:
     AnalysisGraph(const NetworkGraph* ng);
     ~AnalysisGraph();
     void print_graph();
     void print_path(string, string, vector<string> & );
     bool path_has_loop(string, vector<string> &);

     uint64_t convert_mac_str_to_uint64(string);

     void init_adjacent_port_id_map(const NetworkGraph* ng);
     void add_wildcard_rule(AnalysisGraphNode *, AnalysisGraphNode *);
     void init_flow_table_rules(AnalysisGraphNode *, FlowTable, string);
     void init_graph_node_per_host(Host);
     void init_wildcard_rules_per_switch(Switch);
     void init_graph_nodes_per_switch(Switch);
     void init_group_table_per_switch(Switch);
     void init_flow_tables_per_switch(Switch);

     void apply_rule_effect(Vertex, Vertex, AnalysisGraphNode*, policy_match_t*, RuleEffect*, vector<vector<string> > &, vector<string> &, Lmbda);
     void find_packet_paths(Vertex, Vertex, AnalysisGraphNode*, policy_match_t*, vector<vector<string> > &, vector<string> &, Lmbda);
     vector<string> find_path(string, string, policy_match_t, Lmbda);
     double find_time_to_disconnect(const MonteCarloParams*, int);
     vector<double> get_num_active_flows(vector<Flow>, NumActiveFlowsRep);

     analysis_graph g;
     vector<Link> all_switch_links;

     std::unordered_map<string, GroupEffect*> group_effects;
     std::unordered_map<string, string> adjacent_port_id_map;
     
     std::unordered_map<string, Vertex> node_id_vertex_map;
     std::unordered_map<Vertex, AnalysisGraphNode*> vertex_to_node_map;

     

 private:

};


#endif