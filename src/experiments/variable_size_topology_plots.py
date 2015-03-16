import json
import time
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as ss


#Assuming that x-axis are keys to the data_dict

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


def plot_varying_size_topology(init_times, failover_update_times):

    h = []

    if init_times:

        x1, init_times_mean, init_times_sem = get_x_y_err(init_times)

        l_init_times = plt.errorbar(x1, init_times_mean, init_times_sem,
                                    label="Initial", fmt="x", color="black")
        h.append(l_init_times)

    if failover_update_times:
        x2, failover_update_times_mean, failover_update_times_sem = get_x_y_err(failover_update_times)

        l_failover_update_times = plt.errorbar(x2, failover_update_times_mean, failover_update_times_sem,
                                            label="Incremental", fmt="o", color="black")
        h.append(l_failover_update_times)


    plt.legend(handles=h, loc="upper right")
    plt.xlim((2, 22))
    plt.xticks(range(2, 22, 2), fontsize=16)
    plt.yticks(fontsize=16)

    plt.xlabel("Number of switches in the tree", fontsize=18)
    plt.ylabel("Computation Time(ms)", fontsize=18)
    plt.show()


#with open("data/variable_size_topology_ring_data_20150315_143422.json", "r") as infile:
#    data = json.load(infile)


with open("data/variable_size_topology_fat_tree_data_20150316_111603.json", "r") as infile:
    data = json.load(infile)


plot_varying_size_topology(data["init_times"], data["failover_update_times"])
