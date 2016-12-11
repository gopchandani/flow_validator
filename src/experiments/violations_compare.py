import pickle

with open("data/substation_mixed_policy_validation_times_1_iterations_20161211_153725_violations.pickle", "r") as infile:
    v1 = pickle.load(infile)

with open("data/substation_mixed_policy_validation_times_1_iterations_20161211_151003_violations.pickle", "r") as infile:
    v2 = pickle.load(infile)

print "v1:"
for v in v1:
    print v

print "v2:"
for v in v2:
    print v

for v2i in v2:
    for v1i in v1:
        if str(v2i) == str(v1i):
            print "These match"

