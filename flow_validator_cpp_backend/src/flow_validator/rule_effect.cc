#include "rule_effect.h"
#include "analysis_graph.h"
#include "analysis_graph_node.h"

RuleEffect::RuleEffect() {

}

RuleEffect::RuleEffect(AnalysisGraph *ag, Bucket in_bucket, string switch_id) {
    for (int k=0; k < in_bucket.actions_size(); k++) {

        if (in_bucket.actions(k).type() == "OUTPUT") {
            if (in_bucket.actions(k).output_port_num() == OUT_TO_IN_PORT) {
                bolt_back = true;
            } 
            else 
            if (in_bucket.actions(k).output_port_num() == CONTROLLER_PORT) {
            }
            else 
            {
                string node_id =  switch_id + ":" + to_string(in_bucket.actions(k).output_port_num());
                next_node = ag->vertex_to_node_map[ag->node_id_vertex_map[node_id]];
            }
        } 
        else
        if (in_bucket.actions(k).type() == "PUSH_VLAN") {
            packet_modifications["has_vlan_tag"] = 1;
        } 
        else
        if (in_bucket.actions(k).type() == "SET_FIELD") {
            packet_modifications[in_bucket.actions(k).modified_field()] =  in_bucket.actions(k).modified_value();
        } 
        else
        if (in_bucket.actions(k).type() == "POP_VLAN") {
            packet_modifications["has_vlan_tag"] = 0;
        } 
    }        
}

RuleEffect::RuleEffect(AnalysisGraph *ag, Instruction i, string switch_id) {
    next_node = NULL;
    group_effect = NULL;
    bolt_back = false;


    if (i.type() == "APPLY_ACTIONS") {
        for (int k=0; k<i.actions_size(); k++)
        {
            cout << i.actions(k).type() << endl;
            if (i.actions(k).type() == "OUTPUT") {
                if (i.actions(k).output_port_num() == OUT_TO_IN_PORT) {
                    bolt_back = true;
                } 
                else 
                if (i.actions(k).output_port_num() == CONTROLLER_PORT) {
                }
                else 
                {
                    string output_port_node_id =  switch_id + ":" + to_string(i.actions(k).output_port_num());                    
                    AnalysisGraphNode *adjacent_port_node = ag->adjacent_port_node_map[output_port_node_id];
                    next_node = adjacent_port_node;
                    packet_modifications["in_port"] = adjacent_port_node->port_num;
                }
            } 
            else 
            if (i.actions(k).type() == "GROUP") {
                string group_key = switch_id + ":" + to_string(i.actions(k).group_id());

                if (!(ag->group_effects.find(group_key) == ag->group_effects.end())) {
                    group_effect = ag->group_effects[group_key];
                } else
                {
                    cout << "Weird... this group with key: " << group_key << " does not exist." << endl;
                }
            } 
            else
            if (i.actions(k).type() == "PUSH_VLAN") {
                packet_modifications["has_vlan_tag"] = 1;
            } 
            else
            if (i.actions(k).type() == "SET_FIELD") {
                packet_modifications[i.actions(k).modified_field()] =  i.actions(k).modified_value();
            } 
            else
            if (i.actions(k).type() == "POP_VLAN") {
                packet_modifications["has_vlan_tag"] = 0;
            } 
        }
    }
    //TODO
    else 
    if (i.type() == "WRITE_ACTIONS") {
    }
    else 
    if (i.type() == "GOTO_TABLE") {        
        string node_id = switch_id + ":table" + to_string(i.go_to_table_num());
        next_node = ag->vertex_to_node_map[ag->node_id_vertex_map[node_id]];

        cout << "go_to_table_num: " << i.go_to_table_num() << " node_id:" << node_id << " next_node:" << next_node->node_id << endl;

    }
    
}

void RuleEffect::get_modified_policy_match(policy_match_t* match_in) {

    cout << "get_modified_policy_match" << endl;

    policy_match_t::iterator it;
    for (it = packet_modifications.begin(); it != packet_modifications.end(); it++)
    {
        cout << "Applying modification on the field: " << it->first << " to become: " << it->second << endl;
        (*match_in)[it->first] = it->second;
    }

}