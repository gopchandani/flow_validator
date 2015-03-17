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


def plot_number_of_hosts(initial_port_graph_construction_time, initial_traffic_set_propagation_time):

    h = []

    if initial_port_graph_construction_time:

        x1, \
        initial_port_graph_construction_time_mean, \
        initial_port_graph_construction_time_sem = get_x_y_err(initial_port_graph_construction_time)

        l_initial_port_graph_construction_time = plt.errorbar(x1,
                                                              initial_port_graph_construction_time_mean,
                                                              initial_port_graph_construction_time_sem,
                                                              label="Port Graph Construction",
                                                              fmt="s",
                                                              color="black")
        h.append(l_initial_port_graph_construction_time)


    if initial_traffic_set_propagation_time:

        x1, \
        initial_traffic_set_propagation_time_mean, \
        initial_traffic_set_propagation_time_sem = get_x_y_err(initial_traffic_set_propagation_time)

        l_initial_traffic_set_propagation_time = plt.errorbar(x1,
                                                              initial_traffic_set_propagation_time_mean,
                                                              initial_traffic_set_propagation_time_sem,
                                                              label="Initial Traffic Set",
                                                              fmt="x",
                                                              color="black")
        h.append(l_initial_traffic_set_propagation_time)

    plt.legend(handles=h, loc="upper left")
    plt.xlim((0, 22))
    plt.xticks(range(2, 22, 2), fontsize=16)
    plt.yticks(fontsize=16)

    plt.xlabel("Total number of hosts", fontsize=18)
    plt.ylabel("Computation Time(ms)", fontsize=18)
    plt.show()

with open("data/number_of_hosts_data_20150317_102703.json", "r") as infile:
    data = json.load(infile)

plot_number_of_hosts(data["initial_port_graph_construction_time"], data["initial_traffic_set_propagation_time"])
