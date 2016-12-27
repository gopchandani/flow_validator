import pickle

#69 (came from the non-optimized)
with open("data/substation_mixed_policy_validation_times_1_iterations_20161227_145514_violations.pickle", "r") as infile:
    v1 = pickle.load(infile)

#312(came from the optimized)
with open("data/substation_mixed_policy_validation_times_1_iterations_20161227_151030_violations.pickle", "r") as infile:
    v2 = pickle.load(infile)

print len(v1)
print len(v2)

v1s = set([str(x) for x in v1])
v2s = set([str(x) for x in v2])

a = v1s - v2s

print len(a)
if a:
    print "These are not present in v2"
    for v in a:
        print v

b = v2s - v1s
print len(b)
if b:
    print "These are not present in v1"
    for v in b:
        print v