#include "rule.h"

policy_match_t* Rule::get_resulting_policy_match(policy_match_t* match_in) {

    cout << "get_resulting_flow_rule_match: " << flow_rule_match.size() << endl;
    policy_match_t *match_out = match_in;

    cout << (match_in == NULL) << endl;

    flow_rule_match_t::iterator it;
    for (it = flow_rule_match.begin(); it != flow_rule_match.end(); it++)
    {
        cout << "Matching field:" << it->first << endl;
        
        // If the field is present in match_in, check if the range constraint applied by this
        // rule's match allows it
        if (!((*match_in).find(it->first) == (*match_in).end()))
        {
            // Do a range test, if any of the range tests fail, return NULL
            cout << it->first << " " << get<0>(it->second) << " " << get<1>(it->second) << " " << (*match_in)[it->first] << endl;
            cout << ((*match_in)[it->first] >= get<0>(it->second) && (*match_in)[it->first] < get<1>(it->second)) << endl;

            if (!((*match_in)[it->first] >= get<0>(it->second) && (*match_in)[it->first] < get<1>(it->second))) {
                return NULL;
            } 
        }
    }
    return match_out;
}