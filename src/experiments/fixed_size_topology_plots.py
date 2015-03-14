import json
import time
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as ss


def get_x_y_err(data_dict):

    x = sorted(data_dict.keys())

    data_means = []
    data_sems = []

    for p in x:
        mean = np.mean(data_dict[p])
        sem = ss.sem(data_dict[p])
        data_means.append(mean)
        data_sems.append(sem)

    return x, data_means, data_sems

def plot_fixed_size_topology(edges_broken):

    x, edges_broken_mean, edges_broken_sem = get_x_y_err(edges_broken)
    ind = np.arange(len(x))
    width = 0.8

    plt.bar(ind + width, edges_broken_mean, yerr=edges_broken_sem, color="0.90", align='center')

    plt.xticks(ind + width, tuple(x))
    #plt.xticklabels(set(x))
    plt.xlabel("Edge Broken")
    plt.ylabel("Computation Time (ms)")
    plt.show()

# Merge data2 into data1 and return data1
def merge_data_sets(data1, data2):
    data = data1

    for topo_size in data2["edges_broken"]:
        data["edges_broken"][topo_size].extend(data2["edges_broken"][topo_size])

    for topo_size in data2["failover_update_times"]:
        data["failover_update_times"][topo_size].extend(data2["failover_update_times"][topo_size])

    return data
#
# with open("data/data_20150313_134840.json", "r") as infile:
#     data1 = json.load(infile)
#
# with open("data/data_20150313_155810.json", "r") as infile:
#     data2 = json.load(infile)
#
# data = merge_data_sets(data1, data2)

with open("data/fixed_size_topology_data_20150313_175739.json", "r") as infile:
    data = json.load(infile)

plot_fixed_size_topology(data["edges_broken"])
