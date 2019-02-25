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

void AnalysisGraph::find_paths_helper(Vertex v, Vertex t, vector<vector<Vertex> > & pv, vector<Vertex> & p, map<Vertex, default_color_type> & vcm) 
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
