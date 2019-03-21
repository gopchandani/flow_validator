#include "analysis_graph.h"

#include "rule.h"
#include "rule_effect.h"
#include "analysis_graph_node.h"


void AnalysisGraph::init_flow_table_node(AnalysisGraphNode *agn, FlowTable flow_table, string switch_id) {

    for (int i=0; i<flow_table.flow_rules_size(); i++) {

        // Initialize a Rule
        Rule *r = new Rule(flow_table.flow_rules(i).priority());

        // Populate the flow rule match
        for (auto & p : flow_table.flow_rules(i).flow_rule_match()) {
            r->flow_rule_match[p.first] = make_tuple(p.second.value_start(),  p.second.value_end());
        }

        // Populate the rule effects
        for (int i = 0; i < flow_table.flow_rules(i).instructions_size(); i++) {
            RuleEffect rule_effect (this, flow_table.flow_rules(i).instructions(i), switch_id);
            r->rule_effects.push_back(rule_effect);
        }

        agn->rules.push_back(r);
    }
}

void AnalysisGraph::init_graph_per_switch(Switch sw) {

    // Add a node for each port in the graph
    for (int i=0; i < sw.ports_size(); i++) {    

        if (sw.ports(i).port_num() == CONTROLLER_PORT) {
            continue;
        }

        string node_id = sw.switch_id() + ":" + to_string(sw.ports(i).port_num());
        Vertex v = add_vertex(g); 
        AnalysisGraphNode *agn = new AnalysisGraphNode(node_id, sw.ports(i).port_num());

        vertex_to_node_map[v] = agn;
        node_id_vertex_map[node_id] = v;

    }

    for (int i=0; i < sw.group_table_size(); i++) {
        cout << "Group Id: " << sw.group_table(i).id() << " Group Type: " << sw.group_table(i).type() << endl;
    }

    // Add a node for each table in the graph
    for (int i=0; i < sw.flow_tables_size(); i++) {
        string node_id = sw.switch_id() + ":table" + to_string(i);
        Vertex v = add_vertex(g); 
        AnalysisGraphNode *agn = new AnalysisGraphNode(node_id);

        init_flow_table_node(agn, sw.flow_tables(i), sw.switch_id());

        vertex_to_node_map[v] = agn;
        node_id_vertex_map[node_id] = v;
    }

    // Add Rules to each port's node to get all packets to table 0
    for (int i=0; i < sw.ports_size(); i++) {    

        if (sw.ports(i).port_num() == CONTROLLER_PORT) {
            continue;
        }

        string src_node_id = sw.switch_id() + ":" + to_string(sw.ports(i).port_num());
        string dst_node_id = sw.switch_id() + ":table0";
        
        add_wildcard_rule(vertex_to_node_map[node_id_vertex_map[src_node_id]], vertex_to_node_map[node_id_vertex_map[dst_node_id]]);
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

        AnalysisGraphNode *src_node = vertex_to_node_map[s];
        AnalysisGraphNode *dst_node = vertex_to_node_map[t];

        add_wildcard_rule(src_node, dst_node);
    }

}

void AnalysisGraph::add_wildcard_rule(AnalysisGraphNode *src_node, AnalysisGraphNode *dst_node) {
    // Initialize a rule 
    Rule *r = new Rule(1);

    // Populate the rule effects
    RuleEffect *re = new RuleEffect();
    re->next_node = dst_node;
    r->rule_effects.push_back(*re);
    src_node->rules.push_back(r);

    cout << src_node->node_id << " " << src_node->rules.size() << endl;
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

void AnalysisGraph::find_packet_paths(Vertex v, Vertex t, policy_match_t* pm_in, vector<vector<Vertex> > & pv, vector<Vertex> & p, map<Vertex, default_color_type> & vcm) 
{
    AnalysisGraphNode *agn = vertex_to_node_map[v];
    cout << "node_id:" << agn->node_id << endl;

    p.push_back(v);
    vcm[v] = black_color;

    if (v == t) {
        pv.push_back(p);

    } else
    {
        // Go through each rule at this node 
        for (uint i=0; i < agn->rules.size(); i++) {

            // if the rule allows the packets to proceed, follow its effects
            policy_match_t* pm_out = agn->rules[i]->get_resulting_flow_rule_match(pm_in);
            if (pm_out) {

                for (uint j=0; j < agn->rules[i]->rule_effects.size(); j++)
                {
                    cout << "next_node: " << agn->rules[i]->rule_effects[j].next_node->node_id << endl;
                    find_packet_paths(node_id_vertex_map[agn->rules[i]->rule_effects[j].next_node->node_id], t, pm_out, pv, p, vcm);
                }

                // Only match a single rule in a given node
                break;
            }
        }     
 /*
        AdjacencyIterator ai, a_end;         
        for (tie(ai, a_end) = adjacent_vertices(v, g); ai != a_end; ++ai) {
            if (vcm[*ai] == white_color) {
                find_packet_paths(*ai, t, pv, p, vcm);
            } 
        }
*/
    }

    p.pop_back();
    vcm[v] = white_color;
}

void AnalysisGraph::populate_policy_match(AnalysisGraphNode *src_node, AnalysisGraphNode *dst_node, policy_match_t & pm) {

    //pm["ethernet_source"] = ;
    //pm["ethernet_destination"] = ;

    pm["in_port"] = src_node->port_num;
    pm["has_vlan_tag"] = 0;
}

void AnalysisGraph::find_paths(string src, string dst, policy_match_t & pm) {

    Vertex s, t;
    s = node_id_vertex_map[src];
    t = node_id_vertex_map[dst];
    AnalysisGraphNode *src_node = vertex_to_node_map[s];
    AnalysisGraphNode *dst_node = vertex_to_node_map[t];

    populate_policy_match(src_node, dst_node, pm);

    vector<vector<Vertex> > pv;
    vector<Vertex> p;
    vector<vector<Vertex> >::iterator pv_iter;
    vector<Vertex>::iterator p_iter;

    for (auto & field : pm)
    {
        cout << field.first << " " << field.second << endl;
    }

    map<Vertex, default_color_type> vcm;

    cout << "Path: " << src << "->" << dst << endl;

    //find_packet_paths(s, t, &pm, pv, p, vcm);

    for (pv_iter = pv.begin(); pv_iter !=  pv.end(); pv_iter++) {
        for (p_iter = pv_iter->begin(); p_iter != pv_iter->end(); p_iter++) {
            cout << vertex_to_node_map[*p_iter]->node_id << " " ;
        }
        cout << endl;
    }

}
