#include "group_effect.h"
#include "analysis_graph_node.h"

GroupEffect::GroupEffect(Switch sw, Group in_group, AnalysisGraph* ag) {
    ag = ag;
    group_id = in_group.id();
    group_type = in_group.type();
    group_key = sw.switch_id() + ":" + to_string(group_id);

    //cout << "Group Id: " << in_group.id() << " Group Type: " << in_group.type() << " Group Key: " << group_key << " Buckets Size: " << in_group.buckets_size() << endl;
    
    for (int i=0; i < in_group.buckets_size(); i++) {
        string watch_port_node_id = sw.switch_id() + ":" + to_string(in_group.buckets(i).watch_port_num());
        AnalysisGraphNode *watch_port_node = ag->vertex_to_node_map[ag->node_id_vertex_map[watch_port_node_id]];
        watch_port_nodes.push_back(watch_port_node);

        RuleEffect *re = new RuleEffect(ag, in_group.buckets(i), sw.switch_id());

        //cout << "Watch Port: " << watch_port_node->node_id << endl;
        //cout << "Rule Effect: " << (re->next_node == NULL) << endl;
        //cout << "Rule Effect Bolt Back:" << re->bolt_back << endl;
        //cout << "Rule Effect Next Node: " << re->next_node->node_id << endl;

        rule_effects.push_back(re);
        //cout << "Rule Effect: " << i << endl;// << " watch_port_node_id: " << watch_port_node_id << " rule_effect: " << rule_effects[i].next_node->node_id << endl;
    }
    
}

bool is_node_inactive(string node_id, Lmbda l) {

    for (int i=0; i < l.links_size(); i++) {
        string src_port_node_id = l.links(i).src_node() + ":" + to_string(l.links(i).src_port_num());
        string dst_port_node_id = l.links(i).dst_node() + ":" + to_string(l.links(i).dst_port_num());

        if (src_port_node_id == node_id || dst_port_node_id == node_id) {
            return true;
        }
    }
    return false;
}

vector<RuleEffect*> GroupEffect::get_active_rule_effects(Lmbda l) {
    vector<RuleEffect*> active_rule_effects;

    // If the group is a fast-failover then the first active watch port's effect is the only one returned
    if (group_type == "FF") {
        //cout << "Group Id:" << group_id << "Group Type: FF" << endl;
        for (uint32_t i=0; i < rule_effects.size(); i++) {
            //cout << i << " " << watch_port_nodes[i]->node_id << endl;
            if (!is_node_inactive(watch_port_nodes[i]->node_id, l)) {
                active_rule_effects.push_back(rule_effects[i]);
                break;
            }
        }
    } else 
    if (group_type == "ALL") {
        //cout << "Group Id:" << group_id << "Group Type: ALL" << endl;
        for (uint32_t i=0; i < rule_effects.size(); i++) {
            if (!is_node_inactive(watch_port_nodes[i]->node_id, l)) {
                active_rule_effects.push_back(rule_effects[i]);
            }
        }
    }

    return active_rule_effects;
}