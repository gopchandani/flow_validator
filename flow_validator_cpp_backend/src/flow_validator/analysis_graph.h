#ifndef __FLOW_VALIDATOR_BACKEND_SWITCH_GRAPH_H__
#define __FLOW_VALIDATOR_BACKEND_SWITCH_GRAPH_H__

#include "boost/graph/depth_first_search.hpp"
#include "boost/graph/undirected_dfs.hpp"
#include "boost/graph/adjacency_list.hpp"
#include "boost/graph/graphviz.hpp"
#include "proto/flow_validator.grpc.pb.h"

using namespace boost;
using namespace std;
using namespace flow_validator;

typedef property<vertex_name_t, std::string> VertexNameProperty;
typedef adjacency_list< vecS, vecS, undirectedS, VertexNameProperty> analysis_graph;
typedef graph_traits<analysis_graph>::vertex_descriptor Vertex;
typedef graph_traits<analysis_graph>::edge_descriptor Edge;
typedef graph_traits<analysis_graph>::vertex_iterator vertex_iter;
typedef graph_traits<analysis_graph>::edge_iterator edge_iter;
typedef iterator_property_map<vector<default_color_type>::iterator, property_map<analysis_graph, vertex_index_t>::type > PathFinderColorMap;
typedef graph_traits<analysis_graph>::adjacency_iterator AdjacencyIterator;
typedef typename graph_traits<analysis_graph>::vertices_size_type vertices_size_type;


class AnalysisGraph final {
 public:
     AnalysisGraph(const NetworkGraph* ng);
     ~AnalysisGraph();
     void print_graph();
     void find_topological_paths(string, string);
     void find_paths_helper(Vertex, Vertex, const vector<vector<Vertex> > &, const vector<Vertex> &, const map<Vertex, default_color_type> &);
     void find_paths(string, string);

 private:
      analysis_graph g;
      std::unordered_map<string, Vertex> node_id_vertex_map;
      property_map<analysis_graph, vertex_name_t>::type node_id = get(vertex_name, g);
};
#endif