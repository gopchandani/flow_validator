#include "rule.h"

RuleEffect::RuleEffect(Instruction i) {

    if (i.type() == "APPLY_ACTIONS") {
        for (int k=0; k<i.actions_size(); k++)
        {
            cout << i.actions(k).type() << endl;
            if (i.actions(k).type() == "OUTPUT") {
                cout << "Output Port: " << i.actions(k).output_port_num() << endl;

                if (i.actions(k).output_port_num() == OUT_TO_IN_PORT) {
                    cout << "InPort" << endl;
                    bolt_back = true;
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