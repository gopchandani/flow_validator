#ifndef __SDNSIM_COMMON_TYPES_H__
#define __SDNSIM_COMMON_TYPES_H__

#include <unordered_map>
#include <tuple>

using namespace std;

typedef std::unordered_map<string, std::tuple<uint64_t, uint64_t> > flow_rule_match_t;
typedef std::unordered_map<string, uint64_t> policy_match_t;

#endif
