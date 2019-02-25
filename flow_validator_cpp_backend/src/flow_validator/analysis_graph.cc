#include "analysis_graph.h"


AnalysisGraph::AnalysisGraph(const NetworkGraph* ng){
    /*
    for (int i=0; i < ng->switches_size(); i++) {       
        Vertex v = add_vertex(g);
        node_id[v] = ng->switches(i).node_id();
    }
    */

    for (int i=0; i < ng->links_size(); i++) {
        // Check if the nodes already exist, if so, grab their descriptor
        Vertex v1, v2;
        
        if (node_id_vertex_map.count(ng->links(i).src_node()) == 1) {
            v1 = node_id_vertex_map[ng->links(i).src_node()];

        } else {
            v1 = add_vertex(g); 
            node_id_vertex_map[ng->links(i).src_node()] = v1;
            node_id[v1] = ng->links(i).src_node();
        }

        if (node_id_vertex_map.count(ng->links(i).dst_node()) == 1) {
            v2 = node_id_vertex_map[ng->links(i).dst_node()];
        } else {
            v2 = add_vertex(g);
            node_id_vertex_map[ng->links(i).dst_node()] = v2;
            node_id[v2] = ng->links(i).dst_node();
        }
    
        auto existing_edge = edge(v1, v2, g);
        if (!existing_edge.second) {
            add_edge(v1, v2, g);
            cout << "Added link:" << ng->links(i).src_node() << "<->" << ng->links(i).dst_node() << endl;
        }
    }
}

AnalysisGraph::~AnalysisGraph() {
}

void AnalysisGraph::print_graph() {
    // represent graph in DOT format and send to cout
    write_graphviz(cout, g);

    std::pair<vertex_iter, vertex_iter> vp;
    for (vp = vertices(g); vp.first != vp.second; ++vp.first) {
        cout << node_id[*vp.first] << endl;
    }

    // Iterate through the edges and print them out
    std::pair<edge_iter, edge_iter> ep;
    edge_iter ei, ei_end;
    for (tie(ei, ei_end) = edges(g); ei != ei_end; ++ei) {
        std::cout << node_id[source(*ei, g)] << " <-> "  << node_id[target(*ei, g)] << endl;
    }
}


template<typename graph_t>
struct TalkativeVisitor
  : boost::dfs_visitor<>
{
  typedef typename boost::graph_traits<graph_t>::vertex_descriptor vertex_descriptor;
  typedef typename boost::graph_traits<graph_t>::edge_descriptor edge_descriptor;

  // // Commented out to avoid clutter of the output.
  // void discover_vertex(vertex_descriptor u, const graph_t&) { // check!
  //   std::cout << "discover_vertex: " << u << std::endl;
  // }
  // void finish_vertex(vertex_descriptor u, const graph_t&) { // check!
  //     std::cout << "finish_vertex: " << u << std::endl;
  // }
  // void initialize_vertex(vertex_descriptor u, const graph_t&) { // check!
  //     std::cout << "initialize_vertex: " << u << std::endl;
  // }
  // void start_vertex(vertex_descriptor u, const graph_t&) { // check!
  //     std::cout << "start_vertex: " << u << std::endl;
  // }
  void examine_edge(edge_descriptor u, const graph_t&) { // check!
      std::cout << "examine_edge: " << u << std::endl;
  }
  // void tree_edge(edge_descriptor u, const graph_t&) { // check!
  //     std::cout << "tree_edge: " << u << std::endl;
  // }
  // void back_edge(edge_descriptor u, const graph_t&) { // check!
  //     std::cout << "back_edge: " << u << std::endl;
  // }
  // void forward_or_cross_edge(edge_descriptor u, const graph_t&) { // check!
  //     std::cout << "forward_or_cross_edge: " << u << std::endl;
  // }
  void finish_edge(edge_descriptor u, const graph_t&) { // uncalled!
      std::cout << "finish_edge: " << u << std::endl;
  }
};





class PathFinder : public default_dfs_visitor {

    private:
    Vertex t;
    property_map<analysis_graph, vertex_name_t>::type n_id;
    vector<Vertex> p;
    const vector<vector<Vertex> > *paths;

    public: 
    PathFinderColorMap vertex_color_map; 

    PathFinder(Vertex dst, property_map<analysis_graph, vertex_name_t>::type node_id, const vector<vector<Vertex> > & pv, PathFinderColorMap & vcm) {
        vertex_color_map = vcm;
        paths = &pv;
        t = dst;
        n_id = node_id;
    }

    void tree_edge(Edge e, const analysis_graph& g) const {
        return;
    }
    void back_edge(Edge e, const analysis_graph& g) const {
        return;
    }
    void discover_vertex(Vertex v, const analysis_graph& g) const {
        cout << "discover_vertex:" << n_id[v] << " color:" << vertex_color_map[v] << endl;
        p.push_back(v);

        if (t == v) {
            cerr << "Found the destinaton!" << endl;
            paths->push_back(p);

            for (auto const& i: p) {
		        cout << n_id[i] << " ";
	        }
            cout << endl;
        }
        return;
    }

    void examine_edge(Edge e, const analysis_graph& g) const {
        cout << "examine_edge: " << n_id[e.m_source] << "--" << n_id[e.m_target] << endl;
        return;
        
    }

    void finish_edge(Edge e, const analysis_graph& g) const {
        cout << "finish_edge: " << n_id[e.m_source] << "--" << n_id[e.m_target] << endl;
        return;
    }
    
    void finish_vertex(Vertex v, const analysis_graph& g) const {
        cout << "finish_vertex:" << n_id[v] << " color:" << vertex_color_map[v] << endl;

        vertex_color_map[v] = white_color;
        if (!p.empty()) {
            p.pop_back();
        }
        return;
    }

};

void AnalysisGraph::find_topological_paths(string src, string dst) {

    vector<vector<Vertex> > pv;
    
    map<analysis_graph::edge_descriptor, default_color_type> edge_color;
    auto edge_color_map = make_assoc_property_map(edge_color);

    vector<default_color_type> vertex_color(num_vertices(g));
    auto idmap = get(vertex_index, g);
    auto vcm = make_iterator_property_map(vertex_color.begin(), idmap);

    PathFinder path_finder_visitor(node_id_vertex_map[dst], node_id, pv, vcm);
    undirected_dfs(g, path_finder_visitor, path_finder_visitor.vertex_color_map, edge_color_map, node_id_vertex_map[src]);

    // Iterate over the paths that were found and print them
    cout << src << "->" << dst << endl;
    vector<vector<Vertex> >::iterator p;
    vector<Vertex>::iterator n;

    for (p = pv.begin(); p !=  pv.end(); p++) {
        for (n = p->begin(); n != p->end(); n ++) {
            cout << node_id[*n] << " ";
        }
        cout << endl;

    }


    depth_first_search(g, visitor(TalkativeVisitor<analysis_graph>()));
}
void AnalysisGraph::find_paths_helper(Vertex v, Vertex t, const vector<vector<Vertex> > & pv, const vector<Vertex> & p, const map<Vertex, default_color_type> & vcm) 
{
    p.push_back(v);
    vcm[v] = black_color;

    if (v == t) {
        pv.push_back(p);

    } else
    {
        AdjacencyIterator ai, a_end;         
        for (tie(ai, a_end) = adjacent_vertices(v, g); ai != a_end; ++ai) {
            if (vcm[*ai] == white_color) {
                find_paths_helper(*ai, t, pv, p, vcm);
            } 
        }
    }

    p.pop_back();
    vcm[v] = white_color;
}

void AnalysisGraph::find_paths(string src, string dst) {

    vector<vector<Vertex> > pv;
    vector<Vertex> p;

    vector<vector<Vertex> >::iterator pv_iter;
    vector<Vertex>::iterator p_iter;

    cout << src << "->" << dst << endl;

    map<Vertex, default_color_type> vcm;

    find_paths_helper(node_id_vertex_map[src], node_id_vertex_map[dst], pv, p, vcm);

    for (pv_iter = pv.begin(); pv_iter !=  pv.end(); pv_iter++) {
        for (p_iter = pv_iter->begin(); p_iter != pv_iter->end(); p_iter++) {
            cout << node_id[*p_iter] << " ";
        }
        cout << endl;

    }

}
