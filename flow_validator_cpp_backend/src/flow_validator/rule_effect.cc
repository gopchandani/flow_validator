#include "rule_effect.h"
#include "analysis_graph.h"
#include "analysis_graph_node.h"

RuleEffect::RuleEffect() {
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
                    cout << "InPort" << endl;
                    bolt_back = true;
                } else 
                if (i.actions(k).output_port_num() == CONTROLLER_PORT) {
                    cout << "Controller" << endl;
                }
                else 
                {
                    cout << "Output Port: " << i.actions(k).output_port_num() << endl;
                    string node_id =  switch_id + ":" + to_string(i.actions(k).output_port_num());
                    next_node = ag->vertex_to_node_map[ag->node_id_vertex_map[node_id]];
                }
            } else 
            if (i.actions(k).type() == "GROUP") {
                string group_key = switch_id + ":" + to_string(i.actions(k).group_id());
                cout << "Group Key: " << group_key << endl;
                group_effect = ag->group_effects[group_key];

            } else
            if (i.actions(k).type() == "PUSH_VLAN") {
                packet_modifications["has_vlan_tag"] = 1;
            } else
            if (i.actions(k).type() == "SET_FIELD") {
                cout << "Set Field: " << i.actions(k).modified_field() << endl;
                cout << "Set Field Value: " << i.actions(k).modified_value() << endl;
                packet_modifications[i.actions(k).modified_field()] =  i.actions(k).modified_value();
            } else
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