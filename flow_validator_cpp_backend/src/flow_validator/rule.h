#ifndef __FLOW_VALIDATOR_BACKEND_RULE_H__
#define __FLOW_VALIDATOR_BACKEND_RULE_H__


class Rule {
    public:
    int priority;

    Rule(int p) {
        priority = p;
    }
};

class LessThanByPriority
{
    public:
    bool operator()(const Rule* lhs, const Rule* rhs) const
    {
        return lhs->priority < rhs->priority;
    }
};

#endif