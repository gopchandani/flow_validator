#include "analysis_graph.h"

void AnalysisGraph::init_graph_per_switch(Switch sw) {

    // Add a node for each port in the graph
    for (int i=0; i < sw.ports_size(); i++) {    

        if (sw.ports(i).port_num() == CONTROLLER_PORT) {
            continue;
        }

        string node_id = sw.switch_id() + ":" + to_string(sw.ports(i).port_num());
        Vertex v = add_vertex(g); 
        AnalysisGraphNode *agn = new AnalysisGraphNode(node_id, v);
        vertex_to_node_map[v] = agn;
        node_id_vertex_map[node_id] = v;
    }

    // Add a node for each table in the graph
    for (int i=0; i < sw.flow_tables_size(); i++) {
        string node_id = sw.switch_id() + ":table" + to_string(i);
        Vertex v = add_vertex(g); 
        AnalysisGraphNode *agn = new AnalysisGraphNode(node_id, v);
        vertex_to_node_map[v] = agn;
        node_id_vertex_map[node_id] = v;
    }

}

AnalysisGraph::AnalysisGraph(const NetworkGraph* ng){

    for (int i=0; i < ng->switches_size(); i++) {
        init_graph_per_switch(ng->switches(i));
    }

    // Add edges corresponding to the switch-switch links
    for (int i=0; i < ng->links_size(); i++) {

        if (!(ng->links(i).src_node()[0] == 's' && ng->links(i).dst_node()[0] == 's')) {
            continue;
        }

        Vertex s, t;
        string src_node_id, dst_node_id;
        src_node_id = ng->links(i).src_node() + ":" + to_string(ng->links(i).src_port_num());
        dst_node_id = ng->links(i).dst_node() + ":" + to_string(ng->links(i).dst_port_num());

        s = node_id_vertex_map[src_node_id];
        t = node_id_vertex_map[dst_node_id];

        auto existing_edge = edge(s, t, g);
        if (!existing_edge.second) {
            add_edge(s, t, g);
            cout << "Added link:" << src_node_id << "->" << dst_node_id << endl;
        }

        t = node_id_vertex_map[src_node_id];
        s = node_id_vertex_map[dst_node_id];

        existing_edge = edge(s, t, g);
        if (!existing_edge.second) {
            add_edge(s, t, g);
            cout << "Added link: " << dst_node_id << "->" << src_node_id << endl;
        }        
    }
}

AnalysisGraph::~AnalysisGraph() {
}

void AnalysisGraph::print_graph() {
    std::pair<vertex_iter, vertex_iter> vp;
    for (vp = vertices(g); vp.first != vp.second; ++vp.first) {
        cout << vertex_to_node_map[*vp.first]->node_id << endl;
    }

    // Iterate through the edges and print them out
    std::pair<edge_iter, edge_iter> ep;
    edge_iter ei, ei_end;
    for (tie(ei, ei_end) = edges(g); ei != ei_end; ++ei) {
        cout << vertex_to_node_map[source(*ei, g)]->node_id << " -> "  << vertex_to_node_map[target(*ei, g)]->node_id << endl;
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

    vertex_to_node_map[node_id_vertex_map[src]]->interval_map_example();

    find_paths_helper(node_id_vertex_map[src], node_id_vertex_map[dst], pv, p, vcm);

    for (pv_iter = pv.begin(); pv_iter !=  pv.end(); pv_iter++) {
        for (p_iter = pv_iter->begin(); p_iter != pv_iter->end(); p_iter++) {
            cout << vertex_to_node_map[*p_iter]->node_id << " " ;
        }
        cout << endl;
    }

}
