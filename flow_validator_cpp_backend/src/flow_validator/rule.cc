#include "rule.h"

flow_rule_match_t* Rule::get_resulting_flow_rule_match(flow_rule_match_t* match_in) {

    flow_rule_match_t *match_out = new flow_rule_match_t;

    flow_rule_match_t::iterator it;
    for (it = flow_rule_match.begin(); it != flow_rule_match.end(); it++)
    {
        cout << it->first << " " << get<0>(it->second) << get<1>(it->second) << endl;

        // If the field is present in match_in, check if the range constraint applied by this
        // rule's match allows it
        if (flow_rule_match.find(it->first) == flow_rule_match.end()) 
        {
            //TODO:
            // Do a range test, if any of the range tests fail, return NULL

        } 
        // If the field is not present in match_in, then include it in the match_out
        else 
        {
            (*match_out)[it->first] = it->second;
        }
    }


    return match_out;

}