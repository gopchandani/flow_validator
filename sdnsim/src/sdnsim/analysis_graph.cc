#include <random>

#include "analysis_graph.h"
#include "rule.h"
#include "rule_effect.h"
#include "analysis_graph_node.h"
#include "group_effect.h"

void AnalysisGraph::init_flow_table_rules(AnalysisGraphNode *agn, FlowTable flow_table, string switch_id) {

    for (int i=0; i<flow_table.flow_rules_size(); i++) {

        // Initialize a Rule
        Rule *r = new Rule(flow_table.flow_rules(i).priority());
        total_flow_table_rules += 1;

        // Populate the flow rule match
        for (auto & p : flow_table.flow_rules(i).flow_rule_match()) {
            r->flow_rule_match[p.first] = make_tuple(p.second.value_start(),  p.second.value_end() + 1);

            // For matching on VLAN-ID, having vlan tag is a must.
            if (p.first == "vlan_vid") {
                r->flow_rule_match["has_vlan_tag"] = make_tuple(1, 2);

                // If the VLAN-VID is a certain number, it indicates matching on just the existence of a tag and 
                // The vlan-vid being a wildcard. So removing the key...
                if (p.second.value_start() == HAS_VLAN_TAG_MATCH) {
                    r->flow_rule_match.erase(p.first);
                }
            }
        }

        // Populate the rule effects
        for (int j = 0; j < flow_table.flow_rules(i).instructions_size(); j++) {
            RuleEffect *rule_effect = new RuleEffect(this, flow_table.flow_rules(i).instructions(j), switch_id);
            r->rule_effects.push_back(rule_effect);
        }

        agn->rules.push_back(r);

        sort( agn->rules.begin( ), agn->rules.end( ), [ ]( const Rule* lhs, const Rule* rhs )
        {
            return lhs->priority > rhs->priority;
        });
        
    }

    //cout << "Flow Table Node: " << agn->node_id << " Total Flow Rules: " << agn->rules.size() << endl;
}

void AnalysisGraph::init_flow_tables_per_switch(Switch sw) {

    for (int i=0; i < sw.flow_tables_size(); i++) {
        string node_id = sw.switch_id() + ":table" + to_string(sw.flow_tables(i).table_num());
        AnalysisGraphNode *agn = node_id_to_node_map[node_id];
        init_flow_table_rules(agn, sw.flow_tables(i), sw.switch_id());
    }
}

void AnalysisGraph::init_group_table_per_switch(Switch sw) {

    for (int i=0; i < sw.group_table_size(); i++) {
        auto *g = new GroupEffect(sw, sw.group_table(i), this);
        group_effects[g->group_key] = g;
    }
}

void AnalysisGraph::init_graph_node_per_host(Host h) {
    string node_id = h.host_name();
    AnalysisGraphNode *host_node = new AnalysisGraphNode(node_id, h.host_ip(), h.host_mac());
    node_id_to_node_map[node_id] = host_node;
}

void AnalysisGraph::init_graph_nodes_per_switch(Switch sw) {

    // Add a node for each port in the graph
    for (int i=0; i < sw.ports_size(); i++) {    

        if (sw.ports(i).port_num() == LOCAL_PORT) {
            continue;
        }

        string node_id = sw.switch_id() + ":" + to_string(sw.ports(i).port_num());
        AnalysisGraphNode *agn = new AnalysisGraphNode(node_id, sw.ports(i).port_num());
        node_id_to_node_map[node_id] = agn;
    }

    // Add a node for each table in the graph
    for (int i=0; i < sw.flow_tables_size(); i++) {
        string node_id = sw.switch_id() + ":table" + to_string(sw.flow_tables(i).table_num());
        AnalysisGraphNode *agn = new AnalysisGraphNode(node_id);
        node_id_to_node_map[node_id] = agn;
    }
}

void AnalysisGraph::init_wildcard_rules_per_switch(Switch sw) {
    // Add Rules to each port's node to get all packets to table 0
    for (int i=0; i < sw.ports_size(); i++) {    

        if (sw.ports(i).port_num() == LOCAL_PORT || sw.ports(i).port_num() == CONTROLLER_PORT || sw.ports(i).port_num() == OUT_TO_IN_PORT) {
            continue;
        }

        string src_node_id = sw.switch_id() + ":" + to_string(sw.ports(i).port_num());
        string dst_node_id = sw.switch_id() + ":table0";

        add_wildcard_rule(node_id_to_node_map[src_node_id], node_id_to_node_map[dst_node_id]);
    }
}

void AnalysisGraph::init_adjacent_port_id_map(const NetworkGraph* ng) {

    for (int i=0; i < ng->links_size(); i++) {

        string src_node_id, dst_node_id;

        if (!(ng->links(i).src_node()[0] == 's' && ng->links(i).dst_node()[0] == 's')) {
            if (ng->links(i).src_node()[0] != 's') {
                src_node_id = ng->links(i).src_node();
                dst_node_id = ng->links(i).dst_node() + ":" + to_string(ng->links(i).dst_port_num());
            }

            if (ng->links(i).dst_node()[0] != 's') {
                src_node_id = ng->links(i).src_node() + ":" + to_string(ng->links(i).src_port_num());
                dst_node_id = ng->links(i).dst_node();
            }
        }
        else
        {
            src_node_id = ng->links(i).src_node() + ":" + to_string(ng->links(i).src_port_num());
            dst_node_id = ng->links(i).dst_node() + ":" + to_string(ng->links(i).dst_port_num());
        }

        //cout << src_node_id << ":" << dst_node_id << endl;
        //cout << dst_node_id << ":" << src_node_id << endl;

        adjacent_port_id_map[src_node_id] = dst_node_id;
        adjacent_port_id_map[dst_node_id] = src_node_id;
    }
}



AnalysisGraph::AnalysisGraph(const NetworkGraph* ng){


    total_flow_table_rules = 0;

    init_adjacent_port_id_map(ng);

    for (int i=0; i < ng->hosts_size(); i++) {
        init_graph_node_per_host(ng->hosts(i));
    }

    for (int i=0; i < ng->switches_size(); i++) {
        init_graph_nodes_per_switch(ng->switches(i));
    }
    for (int i=0; i < ng->switches_size(); i++) {
        init_wildcard_rules_per_switch(ng->switches(i));
    }
    for (int i=0; i < ng->switches_size(); i++) {
        init_group_table_per_switch(ng->switches(i));
    }
    for (int i=0; i < ng->switches_size(); i++) {
        init_flow_tables_per_switch(ng->switches(i));
    }
    // Add edges corresponding to the links
    for (int i=0; i < ng->links_size(); i++) {

        if (!(ng->links(i).src_node()[0] == 's' && ng->links(i).dst_node()[0] == 's')) {
            
            string switch_port_node_id;
            AnalysisGraphNode *switch_port_node, *host_node;;

            if (ng->links(i).src_node()[0] != 's') {
                host_node = node_id_to_node_map[ng->links(i).src_node()];
                switch_port_node_id = ng->links(i).dst_node() + ":" + to_string(ng->links(i).dst_port_num());
            }

            if (ng->links(i).dst_node()[0] != 's') {
                host_node = node_id_to_node_map[ng->links(i).dst_node()];
                switch_port_node_id = ng->links(i).src_node() + ":" + to_string(ng->links(i).src_port_num());
            }

            switch_port_node = node_id_to_node_map[switch_port_node_id];
            switch_port_node->connected_host = host_node;
            continue;
        }

        all_switch_links.push_back(ng->links(i));

        string src_node_id, dst_node_id;
        AnalysisGraphNode *src_node, *dst_node;

        src_node_id = ng->links(i).src_node() + ":" + to_string(ng->links(i).src_port_num());
        dst_node_id = ng->links(i).dst_node() + ":" + to_string(ng->links(i).dst_port_num());

        src_node = node_id_to_node_map[src_node_id];
        dst_node = node_id_to_node_map[dst_node_id];

        add_wildcard_rule(src_node, dst_node);
        add_wildcard_rule(dst_node, src_node);
    }
}

void AnalysisGraph::add_wildcard_rule(AnalysisGraphNode *src_node, AnalysisGraphNode *dst_node) {
    // Initialize a rule 
    Rule *r = new Rule(1);

    // Populate the rule effects
    RuleEffect *re = new RuleEffect();
    re->next_node = dst_node;
    r->rule_effects.push_back(re);
    src_node->rules.push_back(r);
}

AnalysisGraph::~AnalysisGraph() {
}

void AnalysisGraph::print_path(string src_node, string dst_node, vector<string> & p) {

    cout << "Path: " << src_node << "->" << dst_node << " ";
    for (auto p_iter = p.begin(); p_iter != p.end(); p_iter++) {
        cout << *p_iter << " " ;
    }
    cout << endl;
}

bool AnalysisGraph::is_node_inactive(string node_id, Lmbda l) {

    for (int i=0; i < l.links_size(); i++) {
        string src_port_node_id = l.links(i).src_node() + ":" + to_string(l.links(i).src_port_num());
        string dst_port_node_id = l.links(i).dst_node() + ":" + to_string(l.links(i).dst_port_num());

        if (src_port_node_id == node_id || dst_port_node_id == node_id) {
            return true;
        }
    }
    return false;
}

void AnalysisGraph::apply_rule_effect(AnalysisGraphNode *agn, AnalysisGraphNode *dst_node, AnalysisGraphNode *prev_node, policy_match_t* pm, RuleEffect *re, vector<vector<string> > & pv, vector<string> & p, Lmbda l) {

    re->get_modified_policy_match(pm);

    if (re->next_node != NULL) {

        // If the rule effect has a next_node and that node is inactive right now, then bolt, the link has failed
        if (is_node_inactive(re->next_node->node_id, l)) {
            return;
        }

        //cout << "next_node: " << re->next_node->node_id << endl;
        // This node (agn) can only be a previous node if it belongs to a port.
        if (agn->port_num == -1) {
            // Find the next node, for host ports, this becomes the output port, for others, it is the port at the next switch
            if (adjacent_port_id_map.find(re->next_node->node_id) != adjacent_port_id_map.end()) {
                string adjacent_port_node_id = adjacent_port_id_map[re->next_node->node_id];
                AnalysisGraphNode *adjacent_port_node = node_id_to_node_map[adjacent_port_node_id];
            
                p.push_back(re->next_node->node_id);
                (*pm)["in_port"] = adjacent_port_node->port_num;
                find_packet_paths(adjacent_port_node, dst_node, prev_node, pm, pv, p, l);

            } else 
            {
                find_packet_paths(node_id_to_node_map[re->next_node->node_id], dst_node, prev_node, pm, pv, p, l);
            }
        }
        else 
        {
            find_packet_paths(node_id_to_node_map[re->next_node->node_id], dst_node, agn, pm, pv, p, l);
        }
    } 
    else
    if(re->bolt_back == true) 
    {
        //cout << "bolt_back: " << re->bolt_back << endl;
        // This node (agn) can only be a previous node if it belongs to a port.
        string adjacent_port_node_id = adjacent_port_id_map[prev_node->node_id];
        if (agn->port_num == -1) {
            find_packet_paths(node_id_to_node_map[adjacent_port_node_id], dst_node, prev_node, pm, pv, p, l);
        } 
        else 
        {
            find_packet_paths(node_id_to_node_map[adjacent_port_node_id], dst_node, agn, pm, pv, p, l);
        } 
    }
}


bool AnalysisGraph::path_has_loop(string node_id, vector<string> & p)
{
    uint cnt = 0;
    for (auto n = p.begin(); n != p.end(); n++) {
        if (*n == node_id) {
            cnt ++;
            if (cnt ++ > 3) {
                return true;
            }
        }
    }
    return false;
}

void AnalysisGraph::find_packet_paths(AnalysisGraphNode *agn, AnalysisGraphNode *dst_node, AnalysisGraphNode *prev_node, policy_match_t* pm_in, vector<vector<string> > & pv, vector<string> & p, Lmbda l) 
{
    //cout << "-- node_id:" << agn->node_id << endl;
    if (!path_has_loop(agn->node_id, p)) {
        if (agn->port_num != -1) {
            p.push_back(agn->node_id);
        } 
    } 
    else 
    {
        return;
    }

    if (agn->node_id == dst_node->node_id) {
        pv.push_back(p);
    } 
    else
    {
        // Go through each rule at this node 
        for (uint i=0; i < agn->rules.size(); i++) {

            // if the rule allows the packets to proceed, follow its effects
            policy_match_t* pm_out = agn->rules[i]->get_resulting_policy_match(pm_in);
            if (pm_out) {
                //cout << agn->node_id << " Matched the rule at index: " << i << " with " << agn->rules[i]->rule_effects.size() << " effect(s)."<< endl;
                
                //Apply the modifications and go to other places per the effects
                for (uint j=0; j < agn->rules[i]->rule_effects.size(); j++)
                {
                    apply_rule_effect(agn, dst_node, prev_node, pm_out, agn->rules[i]->rule_effects[j], pv, p, l);
                    if(agn->rules[i]->rule_effects[j]->group_effect != NULL) 
                    {
                        //cout << agn->node_id << " Group Effect from group_id: " << agn->rules[i]->rule_effects[j]->group_effect->group_id << endl;
                        auto active_rule_effects = agn->rules[i]->rule_effects[j]->group_effect->get_active_rule_effects(l);
                        //cout << "Total active rule effects: " << active_rule_effects.size() << endl;

                        for (uint k=0; k < active_rule_effects.size(); k++)
                        {   
                            apply_rule_effect(agn, dst_node, prev_node, pm_out, active_rule_effects[k], pv, p, l);
                        }
                    }
                }
                // Only match a single rule in a given node
                break;
            } else
            {
            }
        }    
    }
    if (agn->port_num != -1) {
        p.pop_back();
    } 
}

uint64_t AnalysisGraph::convert_mac_str_to_uint64(string mac) {
  // Remove colons
  mac.erase(std::remove(mac.begin(), mac.end(), ':'), mac.end());

  // Convert to uint64_t
  return strtoul(mac.c_str(), NULL, 16);
}

vector<string> AnalysisGraph::find_path(string src_node_id, string dst_node_id, policy_match_t pm, Lmbda l) {

    AnalysisGraphNode *src_node = node_id_to_node_map[src_node_id];
    AnalysisGraphNode *dst_node = node_id_to_node_map[dst_node_id];

    // populate policy match
    pm["in_port"] = src_node->port_num;
    pm["has_vlan_tag"] = 0;

    if (src_node->connected_host) {
        pm["eth_src"] = convert_mac_str_to_uint64(src_node->connected_host->host_mac);
        //src_node = src_node->connected_host;
        //s = node_id_vertex_map[src_node->node_id];
    }

    if (dst_node->connected_host) {
        pm["eth_dst"] = convert_mac_str_to_uint64(dst_node->connected_host->host_mac);
        dst_node = dst_node->connected_host;
    }

    vector< vector<string> > pv;
    vector<string> p;
    find_packet_paths(src_node, dst_node, src_node, &pm, pv, p, l);
    if (pv.size() > 0) {
        return pv[0];
    }
    else {
        vector<string> empty_path;
        return empty_path;
    }
}

double AnalysisGraph::find_time_to_disconnect(const MonteCarloParams* mcp, int seed) {

    double time_to_disconnect = 0.0;

    // Initialize active links
    vector <Link> active_links;
    for (int i=0; i < all_switch_links.size(); i++) {
        active_links.push_back(all_switch_links[i]);
    }

    default_random_engine* gen = new default_random_engine(seed);
    gen->seed(seed);

    // Initialize lmbda
    Lmbda lmbda;

    while(active_links.size() > 0) {
        uniform_int_distribution<> unif_dis(0, active_links.size()-1);
        exponential_distribution<double>  exp_dis(active_links.size() * mcp->link_failure_rate());

        // Pick and accumulate the time from now when this chosen link might fail
        auto time_to_fail_link =  exp_dis(*gen);
        time_to_disconnect += time_to_fail_link;
        //cout << "time_to_disconnect: " << time_to_disconnect << endl;

        // Pick a link from the links that are active.
        auto link_to_fail_i = unif_dis(*gen);
        auto link_to_fail = active_links[link_to_fail_i];
        //cout << "Link to fail: " << link_to_fail.src_node() << " -- " << link_to_fail.dst_node() << endl;

        active_links.erase(active_links.begin() + link_to_fail_i);

        // Include the link to the lmbda
        auto l = lmbda.add_links();

        //cout << "this_lmbda size: " << lmbda.links_size() << endl;

        l->set_src_node(link_to_fail.src_node());
        l->set_dst_node(link_to_fail.dst_node());
        l->set_src_port_num(link_to_fail.src_port_num());
        l->set_dst_port_num(link_to_fail.dst_port_num());

        // Check if any of the flows have failed with this lmbda
        for (int i = 0; i < mcp->flows_size() ; i++) {

            string src_port = mcp->flows(i).src_port().switch_id() + ":" + to_string(mcp->flows(i).src_port().port_num());
            string dst_port = mcp->flows(i).dst_port().switch_id() + ":" + to_string(mcp->flows(i).dst_port().port_num());
            //cout << "Src Port: " << src_port << " Dst Port: " << dst_port << endl;
            policy_match_t policy_match;
            for (auto & p : mcp->flows(i).policy_match())
            {
                policy_match[p.first] = p.second;
            }
            auto p = find_path(src_port, dst_port, policy_match, lmbda); 
            //print_path(src_port, dst_port, p);

            // If there is no path, then bolt.
            if (p.size() == 0) {
                return time_to_disconnect;
            }
        }
    }

    return time_to_disconnect;
}

NumActiveFlowsRep AnalysisGraph::get_num_active_flows(int i, vector<Flow> flows, const NumActiveFlowsParams* nafp) {

    NumActiveFlowsRep rep;
    Lmbda lmbda;
    
    for (int j=0; j < nafp->reps(i).link_failure_sequence_size(); j++) {
        // Add link to the lmbda
        auto l = lmbda.add_links();
        l->set_src_node(nafp->reps(i).link_failure_sequence(j).src_node());
        l->set_dst_node(nafp->reps(i).link_failure_sequence(j).dst_node());
        l->set_src_port_num(nafp->reps(i).link_failure_sequence(j).src_port_num());
        l->set_dst_port_num(nafp->reps(i).link_failure_sequence(j).dst_port_num());

        // Count how many flows are active now
        int num_active_flows = 0;
        
        for (int k = 0; k < flows.size() ; k++) {

            string src_port = flows[k].src_port().switch_id() + ":" + to_string(flows[k].src_port().port_num());
            string dst_port = flows[k].dst_port().switch_id() + ":" + to_string(flows[k].dst_port().port_num());
            policy_match_t policy_match;
            for (auto & p : flows[k].policy_match())
            {
                policy_match[p.first] = p.second;
            }

            auto start = chrono::steady_clock::now();
            auto p = find_path(src_port, dst_port, policy_match, lmbda); 
            auto end = chrono::steady_clock::now();
            rep.add_time_taken_per_active_flow_computation(chrono::duration_cast<chrono::nanoseconds>(end - start).count());

            if (p.size() > 0) {
                num_active_flows += 1;
                rep.add_path_lengths(p.size());
            }
        }

        // Add to the output
        auto link = rep.add_link_failure_sequence();
        link->set_src_node(nafp->reps(i).link_failure_sequence(j).src_node());
        link->set_src_port_num(nafp->reps(i).link_failure_sequence(j).src_port_num());
        link->set_dst_node(nafp->reps(i).link_failure_sequence(j).dst_node());
        link->set_dst_port_num(nafp->reps(i).link_failure_sequence(j).dst_port_num());
        rep.add_num_active_flows(num_active_flows);

        /*
        cout << "rep: " << i << " link: " << j << " ";
        cout << "src: " << nafp->reps(i).link_failure_sequence(j).src_node() << " ";
        cout << "dst: " << nafp->reps(i).link_failure_sequence(j).dst_node() << " ";
        cout << "Total Flows: " << flows.size() << " Active Flows: "  << num_active_flows << endl;
        */   
    }

    return rep;
}
