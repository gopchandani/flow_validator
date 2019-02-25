#ifndef __FLOW_VALIDATOR_BACKEND_ANALYSIS_GRAPH_H__
#define __FLOW_VALIDATOR_BACKEND_ANALYSIS_GRAPH_H__

#define CONTROLLER_PORT 4294967294

#include "boost/icl/interval_map.hpp"
#include "boost/graph/depth_first_search.hpp"
#include "boost/graph/undirected_dfs.hpp"
#include "boost/graph/adjacency_list.hpp"
#include "boost/graph/graphviz.hpp"
#include "proto/flow_validator.grpc.pb.h"

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

class AnalysisGraphNode final {
    public:
        string node_id;
        Vertex v;

        AnalysisGraphNode(string, Vertex);
        void interval_map_example();

    private:

};


class AnalysisGraph final {
 public:
     AnalysisGraph(const NetworkGraph* ng);
     ~AnalysisGraph();
     void print_graph();
     void init_graph_per_switch(Switch);
     void find_paths_helper(Vertex, Vertex, vector<vector<Vertex> > &, vector<Vertex> &, map<Vertex, default_color_type> &);
     void find_paths(string, string);

 private:
     analysis_graph g;

     std::unordered_map<string, Vertex> node_id_vertex_map;
     std::unordered_map<Vertex, AnalysisGraphNode*> vertex_to_node_map;

};


#endif