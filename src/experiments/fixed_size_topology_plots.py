import json
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
    width = 0.3

    plt.bar(ind + width, edges_broken_mean, yerr=edges_broken_sem, color="0.90", align='center',
            error_kw=dict(ecolor='gray', lw=2, capsize=5, capthick=2))

    plt.xticks(ind + width, tuple(x))
    plt.xlabel("Edge Broken", fontsize=18)
    plt.ylabel("Computation Time (ms)", fontsize=18)
    plt.show()

with open("data/fixed_size_topology_data_20150314_122548.json", "r") as infile:
#with open("data/fixed_size_topology_data_20150314_124420.json", "r") as infile:
    data = json.load(infile)

plot_fixed_size_topology(data["edges_broken"])
