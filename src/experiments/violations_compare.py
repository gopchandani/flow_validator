import pickle

with open("data/substation_mixed_policy_validation_times_1_iterations_20161211_220227_violations.pickle", "r") as infile:
    v1 = pickle.load(infile)
#119


with open("data/substation_mixed_policy_validation_times_1_iterations_20161213_004637_violations.pickle", "r") as infile:
    v2 = pickle.load(infile)
#117
# lmbda: [('s2', 's1'), ('s4', 's1'), ('s4', 's3')] src_port: s3:1 dst_port: s1:1 constraint: (constraint_type: Connectivity, constraint_params: None)
# lmbda: [('s2', 's1'), ('s4', 's3'), ('s4', 's1')] src_port: s3:1 dst_port: s1:1 constraint: (constraint_type: Connectivity, constraint_params: None)

print len(v1)
print len(v2)

v1s = set([str(x) for x in v1])
v2s = set([str(x) for x in v2])

a = v1s - v2s
b = v2s - v1s

print len(a)
print len(b)

if a:
    print "These are not present in v2"
    for v in a:
        print v

if b:
    print "These are not present in v1"
    for v in b:
        print v