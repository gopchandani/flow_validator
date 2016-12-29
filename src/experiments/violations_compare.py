import pickle
from collections import defaultdict

# 65 (came from the non-optimized)
with open("data/substation_mixed_policy_validation_times_1_iterations_20161229_085937_violations.pickle", "r") as infile:
    non_optimized = pickle.load(infile)

# 65 (came from the optimized)
with open("data/substation_mixed_policy_validation_times_1_iterations_20161229_085235_violations.pickle", "r") as infile:
    optimized = pickle.load(infile)

print "List Length:"
print len(non_optimized)
print len(optimized)

non_optimized_d = defaultdict(int)
optimized_d = defaultdict(int)

for x in optimized:
    optimized_d[str(x)] += 1

for x in non_optimized:
    non_optimized_d[str(x)] += 1

non_optimizeds = set(non_optimized_d.keys())
optimizeds = set(optimized_d.keys())

print "Set Length:"
print len(non_optimizeds)
print len(optimizeds)

a = non_optimizeds - optimizeds
print len(a)
if a:
    print "These are not present in optimized"
    for v in a:
        print v

b = optimizeds - non_optimizeds
print len(b)
if b:
    print "These are not present in non_optimized"
    for v in b:
        print v


# non_optimized_d 4
# "lmbda: (('s2', 's1'), ('s2', 's3'), ('s4', 's1'))
# src_port: s2:1 dst_port: s1:1 constraint: (constraint_type: Connectivity, constraint_params: None)
# counter_example:-----\r\n" (139932865966992)

# optimized_d 1
# "lmbda: (('s2', 's1'), ('s2', 's3'), ('s4', 's1'))
#src_port: s2:1 dst_port: s1:1 constraint: (constraint_type: Connectivity, constraint_params: None)
# counter_example:-----\r\n" (139932867472600)