#include "rule_effect.h"
#include "analysis_graph.h"

RuleEffect::RuleEffect() {
}

RuleEffect::RuleEffect(AnalysisGraph *ag, Instruction i, string switch_id) {

    if (i.type() == "APPLY_ACTIONS") {
        for (int k=0; k<i.actions_size(); k++)
        {
            cout << i.actions(k).type() << endl;
            if (i.actions(k).type() == "OUTPUT") {
                cout << "Output Port: " << i.actions(k).output_port_num() << endl;

                if (i.actions(k).output_port_num() == OUT_TO_IN_PORT) {
                    cout << "InPort" << endl;
                    bolt_back = true;
                } else {
                    string node_id =  switch_id + ":" + to_string(i.actions(k).output_port_num());
                    next_node = ag->vertex_to_node_map[ag->node_id_vertex_map[node_id]];
                }

            } else 
            if (i.actions(k).type() == "GROUP") {
                cout << "Group Id: " << i.actions(k).group_id() << endl;
            } else
            if (i.actions(k).type() == "PUSH_VLAN") {
                
            } else
            if (i.actions(k).type() == "SET_FIELD") {
                cout << "Set Field: " << i.actions(k).modified_field() << endl;
                cout << "Set Field Value: " << i.actions(k).modified_value() << endl;
                packet_modifications[i.actions(k).modified_field()] =  i.actions(k).modified_value();
            } else
            if (i.actions(k).type() == "POP_VLAN") {

            } 
        }
    }
    //TODO
    else 
    if (i.type() == "WRITE_ACTIONS") {
    }
    else 
    if (i.type() == "GOTO_TABLE") {
    }
    
}