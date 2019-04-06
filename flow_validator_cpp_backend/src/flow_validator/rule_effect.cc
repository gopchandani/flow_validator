#include "rule_effect.h"
#include "analysis_graph.h"
#include "analysis_graph_node.h"

RuleEffect::RuleEffect() {
    next_node = NULL;
    group_effect = NULL;
    bolt_back = false;
}

RuleEffect::RuleEffect(AnalysisGraph *ag, Bucket in_bucket, string switch_id) {
    next_node = NULL;
    group_effect = NULL;
    bolt_back = false;

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
                // Setup the next node, for host ports, this becomes the output port, for others, it is the port at the next switch
                string output_port_node_id =  switch_id + ":" + to_string(in_bucket.actions(k).output_port_num());             
                string adjacent_port_node_id = ag->adjacent_port_id_map[output_port_node_id];
                AnalysisGraphNode *adjacent_port_node = ag->vertex_to_node_map[ag->node_id_vertex_map[adjacent_port_node_id]];

                //cout << "output_port_node_id: " << output_port_node_id << " adjacent_port_node_id: " << adjacent_port_node_id << endl;
                //cout << "adjacent vertex:" << ag->node_id_vertex_map[adjacent_port_node_id] << endl;
                //cout << "adjacent_port_node: " << adjacent_port_node->node_id << endl;

                if (adjacent_port_node == NULL)
                {
                    next_node = ag->vertex_to_node_map[ag->node_id_vertex_map[output_port_node_id]];
                } else
                {
                    //cout << output_port_node_id << " adjacent_port_node:" << adjacent_port_node->node_id << endl;
                    next_node = adjacent_port_node;
                    packet_modifications["in_port"] = adjacent_port_node->port_num;
                }

                //cout << "next_node: " << next_node->node_id << endl;
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
            //cout << i.actions(k).type() << endl;
            if (i.actions(k).type() == "OUTPUT") {
                if (i.actions(k).output_port_num() == OUT_TO_IN_PORT) {
                    bolt_back = true;
                } 
                else 
                if (i.actions(k).output_port_num() == CONTROLLER_PORT) {
                }
                else 
                {
                    // Setup the next node, for host ports, this becomes the output port, for others, it is the port at the next switch
                    string output_port_node_id =  switch_id + ":" + to_string(i.actions(k).output_port_num());             
                    string adjacent_port_node_id = ag->adjacent_port_id_map[output_port_node_id];
                    AnalysisGraphNode *adjacent_port_node = ag->vertex_to_node_map[ag->node_id_vertex_map[adjacent_port_node_id]];

                    //cout << "output_port_node_id: " << output_port_node_id << " adjacent_port_node_id: " << adjacent_port_node_id << endl;
                    //cout << "adjacent vertex:" << ag->node_id_vertex_map[adjacent_port_node_id] << endl;
                    //cout << "adjacent_port_node: " << adjacent_port_node->node_id << endl;

                    if (adjacent_port_node == NULL)
                    {
                        next_node = ag->vertex_to_node_map[ag->node_id_vertex_map[output_port_node_id]];
                    } else
                    {
                        next_node = adjacent_port_node;
                        packet_modifications["in_port"] = adjacent_port_node->port_num;
                    }

                    //cout << "next_node: " << next_node->node_id << endl;
                }
            } 
            else 
            if (i.actions(k).type() == "GROUP") {
                string group_key = switch_id + ":" + to_string(i.actions(k).group_id());

                if (!(ag->group_effects.find(group_key) == ag->group_effects.end())) {
                    group_effect = ag->group_effects[group_key];
                } else
                {
                    //cout << "Weird... this group with key: " << group_key << " does not exist." << endl;
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
        //cout << "go_to_table_num: " << i.go_to_table_num() << " node_id:" << node_id << " next_node:" << next_node->node_id << endl;
    }
    
}

void RuleEffect::get_modified_policy_match(policy_match_t* match_in) {

    policy_match_t::iterator it;
    for (it = packet_modifications.begin(); it != packet_modifications.end(); it++)
    {
        cout << "Applying modification on the field: " << it->first << " to become: " << it->second << endl;
        (*match_in)[it->first] = it->second;
    }
}