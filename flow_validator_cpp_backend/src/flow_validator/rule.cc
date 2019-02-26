#include "rule.h"


RuleMatch::RuleMatch(const FlowRuleMatch & frm) {
    for (auto & p : frm.fields())
    {
        fields[p.first] = make_tuple(p.second.value_start(),  p.second.value_end());
    }
}