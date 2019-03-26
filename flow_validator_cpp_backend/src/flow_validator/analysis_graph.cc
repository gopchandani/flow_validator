#include "analysis_graph.h"
#include "rule.h"
#include "rule_effect.h"
#include "analysis_graph_node.h"
#include "group_effect.h"

void AnalysisGraph::init_flow_table_rules(AnalysisGraphNode *agn, FlowTable flow_table, string switch_id) {

    cout << "init_flow_table_rules for node: " << agn->node_id << endl;

    for (int i=0; i<flow_table.flow_rules_size(); i++) {

        // Initialize a Rule
        Rule *r = new Rule(flow_table.flow_rules(i).priority());

        // Populate the flow rule match
        for (auto & p : flow_table.flow_rules(i).flow_rule_match()) {
            cout << p.first << " " << p.second.value_start() << " " << p.second.value_end() + 1 <<endl;
            r->flow_rule_match[p.first] = make_tuple(p.second.value_start(),  p.second.value_end() + 1);

            // For matching on VLAN-ID, having vlan tag is a must.
            if (p.first == "vlan_vid") {
                r->flow_rule_match["has_vlan_tag"] = make_tuple(1, 2);
            }
        }

        // Populate the rule effects
        for (int j = 0; j < flow_table.flow_rules(i).instructions_size(); j++) {
            RuleEffect rule_effect(this, flow_table.flow_rules(i).instructions(j), switch_id);
            r->rule_effects.push_back(rule_effect);
        }

        cout << "# rule match fields: " << r->flow_rule_match.size() << " # rule effects: " << r->rule_effects.size() <<endl;
        agn->rules.push_back(r);

        sort( agn->rules.begin( ), agn->rules.end( ), [ ]( const Rule* lhs, const Rule* rhs )
        {
            return lhs->priority > rhs->priority;
        });
        
    }

    cout << "Flow Table Node: " << agn->node_id << " Total Flow Rules: " << agn->rules.size() << endl;
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
        auto *g = new GroupEffect(sw, sw.group_table(i), this);
        group_effects[g->group_key] = g;
    }

    // Add a node for each table in the graph
    for (int i=0; i < sw.flow_tables_size(); i++) {
        string node_id = sw.switch_id() + ":table" + to_string(sw.flow_tables(i).table_num());
        Vertex v = add_vertex(g); 
        AnalysisGraphNode *agn = new AnalysisGraphNode(node_id);
        vertex_to_node_map[v] = agn;
        node_id_vertex_map[node_id] = v;
    }

    for (int i=0; i < sw.flow_tables_size(); i++) {
        string node_id = sw.switch_id() + ":table" + to_string(sw.flow_tables(i).table_num());
        AnalysisGraphNode *agn = vertex_to_node_map[node_id_vertex_map[node_id]];
        init_flow_table_rules(agn, sw.flow_tables(i), sw.switch_id());
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

    for (int i=0; i < ng->hosts_size(); i++) {
        cout << "Host: " << ng->hosts(i).host_name() << " " << ng->hosts(i).host_ip() << " " << ng->hosts(i).host_mac() << endl;
        hosts[ng->hosts(i).host_name()] = ng->hosts(i);
    }

    // Add edges corresponding to the switch-switch links
    for (int i=0; i < ng->links_size(); i++) {

        if (!(ng->links(i).src_node()[0] == 's' && ng->links(i).dst_node()[0] == 's')) {
            
            string switch_port_node_id;
            AnalysisGraphNode *switch_port_node;
            Host *host_node;

            if (ng->links(i).src_node()[0] != 's') {
                host_node = &hosts[ng->links(i).src_node()];
                switch_port_node_id = ng->links(i).dst_node() + ":" + to_string(ng->links(i).dst_port_num());
            }

            if (ng->links(i).dst_node()[0] != 's') {
                host_node = &hosts[ng->links(i).dst_node()];
                switch_port_node_id = ng->links(i).src_node() + ":" + to_string(ng->links(i).src_port_num());
            }

            cout << "switch_port_node_id:" << switch_port_node_id << endl;
            cout << "Host: " << host_node->host_name() << " " << host_node->host_ip() << " " << host_node->host_mac() << endl;

            switch_port_node = vertex_to_node_map[node_id_vertex_map[switch_port_node_id]];
            switch_port_node->connected_host = host_node;
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

    cout << "wildcard:" << src_node->node_id << "->" << dst_node->node_id << endl;
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

void AnalysisGraph::apply_rule_effect(Vertex t, policy_match_t* pm, RuleEffect re, vector<vector<Vertex> > & pv, vector<Vertex> & p, map<Vertex, default_color_type> & vcm) {
    re.get_modified_policy_match(pm);

    if (re.next_node != NULL) {
        cout << "next_node: " << re.next_node->node_id << endl;
        find_packet_paths(node_id_vertex_map[re.next_node->node_id], t, pm, pv, p, vcm);
    } 
    else
    if(re.bolt_back == true) 
    {
        cout << "bolt_back: " << re.bolt_back << endl;
    }
}

void AnalysisGraph::find_packet_paths(Vertex v, Vertex t, policy_match_t* pm_in, vector<vector<Vertex> > & pv, vector<Vertex> & p, map<Vertex, default_color_type> & vcm) 
{
    AnalysisGraphNode *agn = vertex_to_node_map[v];
    cout << "-- node_id:" << agn->node_id << endl;

    p.push_back(v);
    vcm[v] = black_color;

    if (v == t) {
        pv.push_back(p);

    } else
    {
        // Go through each rule at this node 
        for (uint i=0; i < agn->rules.size(); i++) {
            cout << "Trying rule:" << i << " priority:" <<  agn->rules[i]->priority <<endl;

            // if the rule allows the packets to proceed, follow its effects
            policy_match_t* pm_out = agn->rules[i]->get_resulting_policy_match(pm_in);
            if (pm_out) {
                cout << "Matched the rule with " << agn->rules[i]->rule_effects.size() << " effect(s)."<< endl;
                
                //Apply the modifications and go to other places per the effects
                for (uint j=0; j < agn->rules[i]->rule_effects.size(); j++)
                {
                    //if (agn->rules[i]->rule_effects[j].group_effect == NULL) {

                        agn->rules[i]->rule_effects[j].get_modified_policy_match(pm_out);

                        if (agn->rules[i]->rule_effects[j].next_node != NULL) {
                            cout << "next_node: " << agn->rules[i]->rule_effects[j].next_node->node_id << endl;
                            find_packet_paths(node_id_vertex_map[agn->rules[i]->rule_effects[j].next_node->node_id], t, pm_out, pv, p, vcm);
                        } 
                        else
                        if(agn->rules[i]->rule_effects[j].bolt_back == true) 
                        {
                            cout << " bolt_back: " << agn->rules[i]->rule_effects[j].bolt_back << endl;
                        } 

                    //}
                    else
                    if(agn->rules[i]->rule_effects[j].group_effect != NULL) 
                    {
                        cout << "group_effect: " << agn->rules[i]->rule_effects[j].group_effect << endl;
                        cout << "group_effect key: " << agn->rules[i]->rule_effects[j].group_effect->group_key << endl;

                        auto active_rule_effects = agn->rules[i]->rule_effects[j].group_effect->get_active_rule_effects();
                        cout << "active_rule_effects: " << active_rule_effects.size() << endl;
                        
                        for (uint k=0; k < active_rule_effects.size(); j++)
                        {
                            apply_rule_effect(t, pm_out, active_rule_effects[k], pv, p, vcm);
                        }
                    }
                }
                
                // Only match a single rule in a given node
                break;
            } else
            {
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

uint64_t AnalysisGraph::convert_mac_str_to_uint64(string mac) {
  // Remove colons
  mac.erase(std::remove(mac.begin(), mac.end(), ':'), mac.end());

  // Convert to uint64_t
  return strtoul(mac.c_str(), NULL, 16);
}

void AnalysisGraph::populate_policy_match(AnalysisGraphNode *src_node, AnalysisGraphNode *dst_node, policy_match_t & pm) {

    pm["in_port"] = src_node->port_num;
    pm["has_vlan_tag"] = 0;

    if (src_node->connected_host) {
        pm["eth_src"] = convert_mac_str_to_uint64(src_node->connected_host->host_mac());
    }

    if (dst_node->connected_host) {
        pm["eth_dst"] = convert_mac_str_to_uint64(dst_node->connected_host->host_mac());
    }
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

    find_packet_paths(s, t, &pm, pv, p, vcm);

    for (pv_iter = pv.begin(); pv_iter !=  pv.end(); pv_iter++) {
        for (p_iter = pv_iter->begin(); p_iter != pv_iter->end(); p_iter++) {
            cout << vertex_to_node_map[*p_iter]->node_id << " " ;
        }
        cout << endl;
    }

}
