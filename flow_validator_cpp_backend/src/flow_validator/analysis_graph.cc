#include "analysis_graph.h"


AnalysisGraph::AnalysisGraph(const NetworkGraph* ng){
    /*
    for (int i=0; i < ng->switches_size(); i++) {       
        Vertex v = add_vertex(g);
        switch_id[v] = ng->switches(i).switch_id();
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
            switch_id[v1] = ng->links(i).src_node();
        }

        if (node_id_vertex_map.count(ng->links(i).dst_node()) == 1) {
            v2 = node_id_vertex_map[ng->links(i).dst_node()];
        } else {
            v2 = add_vertex(g);
            node_id_vertex_map[ng->links(i).dst_node()] = v2;
            switch_id[v2] = ng->links(i).dst_node();
        }
    
        add_edge(v1, v2, g);

        cout << "Added link:" << ng->links(i).src_node() << "<->" << ng->links(i).dst_node() << endl;
    }
}

AnalysisGraph::~AnalysisGraph() {
}

void AnalysisGraph::print_graph() {
    // represent graph in DOT format and send to cout
    write_graphviz(cout, g);

    std::pair<vertex_iter, vertex_iter> vp;
    for (vp = vertices(g); vp.first != vp.second; ++vp.first) {
        cout << switch_id[*vp.first] << endl;
    }

    // Iterate through the edges and print them out
    std::pair<edge_iter, edge_iter> ep;
    edge_iter ei, ei_end;
    for (tie(ei, ei_end) = edges(g); ei != ei_end; ++ei) {
        std::cout << switch_id[source(*ei, g)] << " <-> "  << switch_id[target(*ei, g)] << endl;
    }
}

class PathFinder : public default_dfs_visitor {

    private:
    Vertex t;
    property_map<analysis_graph, vertex_name_t>::type sw_id;
    vector<Vertex> p;
    vector<vector<Vertex> > *paths;

    public: 
    PathFinderColorMap vertex_color_map; 

    PathFinder(Vertex dst, property_map<analysis_graph, vertex_name_t>::type switch_id, const vector<vector<Vertex> > & pv, PathFinderColorMap & vcm) {
        vertex_color_map = vcm;
        paths = &pv;
        t = dst;
        sw_id = switch_id;
    }

    void tree_edge(Edge e, const analysis_graph& g) const {
        //cerr << "tree_edge: " << sw_id[e.m_source] << "--" << sw_id[e.m_target] << endl;
        return;
    }
    void back_edge(Edge e, const analysis_graph& g) const {
        return;
    }
    void discover_vertex(Vertex v, const analysis_graph& g) const {
        cerr << "Discover Vertex:" << sw_id[v] << " color:" << vertex_color_map[v] << endl;
        p.push_back(v);

        if (t == v) {
            cerr << "Found the destinaton!" << endl;
            paths->push_back(p);

            for (auto const& i: p) {
		        cout << sw_id[i] << " ";
	        }
            cout << endl;

            int a;
            cin >> a;
        }
        return;
    }

    void examine_edge(Edge e, const analysis_graph& g) const {
        cerr << "examine_edge: " << sw_id[e.m_source] << "--" << sw_id[e.m_target] << endl;
        return;
        
    }

    void finish_edge(Edge e, const analysis_graph& g) const {
        cerr << "finish_edge: " << sw_id[e.m_source] << "--" << sw_id[e.m_target] << endl;

        return;
        
    }
    void finish_vertex(Vertex v, const analysis_graph& g) const {
        cerr << "Finish Vertex:" << sw_id[v] << " color:" << vertex_color_map[v] << endl;

        //vertex_color_map[v] = white_color;
        if (!p.empty()) {
            p.pop_back();
        }
        return;
    }

};

void AnalysisGraph::find_topological_paths(std::string src, std::string dst) {

    vector<vector<Vertex> > pv;
    
    map<analysis_graph::edge_descriptor, default_color_type> edge_color;
    auto edge_color_map = make_assoc_property_map(edge_color);

    vector<default_color_type> vertex_color(num_vertices(g));
    auto idmap = get(vertex_index, g);
    auto vcm = make_iterator_property_map(vertex_color.begin(), idmap);

    PathFinder path_finder_visitor(node_id_vertex_map[dst], switch_id, pv, vcm);
    undirected_dfs(g, path_finder_visitor, path_finder_visitor.vertex_color_map, edge_color_map, node_id_vertex_map[src]);

    // Iterate over the paths that were found and print them
    cout << src << "->" << dst << endl;
    vector<vector<Vertex> >::iterator p;
    vector<Vertex>::iterator n;

    for (p = pv.begin(); p !=  pv.end(); p++) {
        for (n = p->begin(); n != p->end(); n ++) {
            cout << switch_id[*n] << " ";
        }
        cout << endl;
    }

}