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


def plot_number_of_hosts(initial_port_graph_construction_time):

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

    plt.xlim((0, 22))
    plt.xticks(range(2, 22, 2), fontsize=16)
    plt.yticks(fontsize=16)

    plt.xlabel("Total number of hosts", fontsize=18)
    plt.ylabel("Port Graph Construction Time(ms)", fontsize=18)
    plt.show()

def merge_data(data1, data2):

    data_initial_port_graph_construction_time = {}
    data_initial_traffic_set_propagation_time = {}

#    for key in

    data = {
        "initial_port_graph_construction_time":
            data1["initial_port_graph_construction_time"] + data2["initial_port_graph_construction_time"],
        "initial_traffic_set_propagation_time":
            data1["initial_traffic_set_propagation_time"] + data2["initial_traffic_set_propagation_time"]
    }

    return data


#
# with open("data/number_of_hosts_data_20150317_174602.json", "r") as infile:
#     data = json.load(infile)
#
# plot_number_of_hosts(data["initial_port_graph_construction_time"])
#
#
#
#
#
# with open("data/number_of_hosts_data_20150317_143425.json", "r") as infile:
#     data1 = json.load(infile)
#
# with open("data/number_of_hosts_data_20150317_174602.json", "r") as infile:
#     data = json.load(infile)
#
# ipgct1 = data1["initial_port_graph_construction_time"]
# ipgct = data["initial_port_graph_construction_time"]
#
# for key in ipgct:
#     if key in ipgct1:
#         ipgct[key].extend(ipgct1[key])
#
# plot_number_of_hosts(ipgct)





#with open("data/number_of_hosts_data_20150330_131129.json", "r") as infile:

with open("data/number_of_hosts_data_20150517_161410.json", "r") as infile:
    ipgct = json.load(infile)["initial_port_graph_construction_time"]


plot_number_of_hosts(ipgct)
