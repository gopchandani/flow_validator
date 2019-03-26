#include "group_effect.h"
#include "analysis_graph_node.h"

GroupEffect::GroupEffect(Switch sw, Group in_group, AnalysisGraph* ag) {
    ag = ag;
    group_id = in_group.id();
    group_type = in_group.type();
    group_key = sw.switch_id() + ":" + to_string(group_id);

    for (int i=0; i < in_group.buckets_size(); i++) {
        string watch_port_node_id = sw.switch_id() + ":" + to_string(in_group.buckets(i).watch_port_num());
        AnalysisGraphNode *watch_port_node = ag->vertex_to_node_map[ag->node_id_vertex_map[watch_port_node_id]];

        watch_port_nodes.push_back(watch_port_node);
        rule_effects.push_back(RuleEffect(ag, in_group.buckets(i), sw.switch_id()));
    }

    cout << "Group Id: " << in_group.id() << " Group Type: " << in_group.type() << " Group Key: " << group_key << endl;
}

vector<RuleEffect> GroupEffect::get_active_rule_effects() {
    vector<RuleEffect> active_rule_effects;


    // If the group is a fast-failover then the first active watch port's effect is the only one returned
    if (group_type == "FF") {
        for (uint32_t i=0; i < rule_effects.size(); i++) {
            if (watch_port_nodes[i]->is_live == true) {
                active_rule_effects.push_back(rule_effects[i]);
                break;
            }
        }
    } else 
    if (group_type == "ALL") {
        for (uint32_t i=0; i < rule_effects.size(); i++) {
            active_rule_effects.push_back(rule_effects[i]);
        }
    }

    return active_rule_effects;
}