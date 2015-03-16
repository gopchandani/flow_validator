import json
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


def plot_varying_number_of_hosts(initial_port_graph_construction_time, initial_traffic_set_propagation_time):

    h = []

    if initial_port_graph_construction_time:

        x1, initial_port_graph_construction_time_mean, initial_port_graph_construction_time_sem = get_x_y_err(initial_port_graph_construction_time)

        l_initial_port_graph_construction_time_sem = plt.errorbar(x1, initial_port_graph_construction_time_mean,
                                                              initial_port_graph_construction_time_sem,
                                                              label="Port Graph Construction", fmt="s", color="black")
        h.append(l_initial_port_graph_construction_time_sem)

    if initial_traffic_set_propagation_time:
        x2, initial_traffic_set_propagation_time_mean, initial_traffic_set_propagation_time_sem = get_x_y_err(initial_traffic_set_propagation_time)

        l_initial_traffic_set_propagation_time = plt.errorbar(x2, initial_traffic_set_propagation_time_mean,
                                                             initial_traffic_set_propagation_time_sem,
                                                             label="Initial Traffic Set", fmt="x", color="black")
        h.append(l_initial_traffic_set_propagation_time)


    plt.legend(handles=h, loc="upper right")
    plt.xlim((2, 22))
    plt.xticks(range(2, 22, 2), fontsize=16)
    plt.yticks(fontsize=16)

    plt.xlabel("Number of switches in the tree", fontsize=18)
    plt.ylabel("Computation Time(ms)", fontsize=18)
    plt.show()


with open("data/variable_size_topology_ring_data_20150315_143422.json", "r") as infile:
    data = json.load(infile)


#with open("data/variable_size_topology_fat_tree_data_20150316_111603.json", "r") as infile:
#    data = json.load(infile)


plot_varying_size_topology(data["initial_traffic_set_propagation_time"], data["failover_property_verification_time"])
