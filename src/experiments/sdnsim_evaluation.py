import sys
import json
import numpy as np
import scipy.stats as ss
from experiment import Experiment
from experiments.network_configuration import NetworkConfiguration
from analysis.sdnsim_client import SDNSimClient
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

__author__ = 'Rakesh Kumar'

sys.path.append("./")


class WSC(Experiment):

    def __init__(self, nc, experiment_data, flow_specs, reps):

        super(WSC, self).__init__("playground", 1)

        self.sdnsim_client = SDNSimClient(nc)

        self.nc = nc
        self.nc.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1, flow_specs=flow_specs)

        self.experiment_data = experiment_data
        self.flow_specs = flow_specs
        self.reps = reps

    def trigger(self, num_iters):

        init_times = []
        active_flow_times = []
        path_lengths = []
        total_times = []
        num_active_flows = []

        for i in xrange(num_iters):

            print "Running iter: ", i+1, "of", num_iters

            init_time = self.sdnsim_client.initialize_sdnsim()

            src_ports, dst_ports, policy_matches = [], [], []

            for i in xrange(len(self.flow_specs["src_hosts"])):
                src_h_obj = self.nc.ng.get_node_object(self.flow_specs["src_hosts"][i])
                dst_h_obj = self.nc.ng.get_node_object(self.flow_specs["dst_hosts"][i])

                src_ports.append((src_h_obj.sw.node_id, src_h_obj.switch_port.port_number))
                dst_ports.append((dst_h_obj.sw.node_id, dst_h_obj.switch_port.port_number))

                policy_matches.append({"eth_type": 0x0800})

                # self.nc.is_host_pair_pingable(self.nc.mininet_obj.get(src_h_obj.node_id),
                #                               self.nc.mininet_obj.get(dst_h_obj.node_id))

            nafi = self.sdnsim_client.get_num_active_flows_when_links_fail(self.reps, src_ports, dst_ports, policy_matches)

            for i in xrange(len(nafi.reps)):
                active_flow_times.extend(nafi.reps[i].time_taken_per_active_flow_computation)
                path_lengths.extend(nafi.reps[i].path_lengths)
                num_active_flows.extend(nafi.reps[i].num_active_flows)

            init_times.append(init_time)
            total_times.append(nafi.time_taken)

        return {"init_times": init_times,
                "active_flow_times": active_flow_times,
                "total_times": total_times,
                "path_lengths": path_lengths,
                "num_active_flows": num_active_flows}

    def same_paths(self, p1, p2):

        # If one exists and other doesn't, not same
        if (p1 and not p2) or (not p1 and p2):
            return False

        # If both do not exist, same path
        if not p1 and not p2:
            return True

        # The existing paths have to have same length, if not, not same
        if len(p1) != len(p2):
            return False

        # Each node need to match, if not, not same
        for i, n in enumerate(p1):
            if p1[i] != p2[i]:
                return False

        return True

    def get_active_synthesized_flow_when_links_fail(self, s_host, t_host, lmbda):

        def path_has_link(path, link):
            for i in xrange(len(path) - 1):
                n1 = path[i].split(":")[0]
                n2 = path[i+1].split(":")[0]
                if (link[0] == n1 and link[1] == n2) or (link[0] == n2 and link[1] == n1):
                    return True

            return False

        if not self.nc.load_config and self.nc.save_config:
            synthesized_primary_paths = self.nc.synthesis.synthesis_lib.synthesized_primary_paths
            synthesized_failover_paths = self.nc.synthesis.synthesis_lib.synthesized_failover_paths
        else:
            with open(self.nc.conf_path + "synthesized_primary_paths.json", "r") as in_file:
                synthesized_primary_paths = json.loads(in_file.read())

            with open(self.nc.conf_path + "synthesized_failover_paths.json", "r") as in_file:
                synthesized_failover_paths = json.loads(in_file.read())

        primary_path = synthesized_primary_paths[s_host][t_host]
        failover_paths = synthesized_failover_paths[s_host][t_host]

        # Check if the failed_links have at least one link in the primary path
        for failed_link_1 in lmbda:

            if path_has_link(primary_path, failed_link_1):

                # If so, it would kick up a failover path
                try:
                    failover_path = failover_paths[failed_link_1[0]][failed_link_1[1]]
                except KeyError:
                    failover_path = failover_paths[failed_link_1[1]][failed_link_1[0]]

                # In the failover path, if there is a link that is in the failed_links
                for failed_link_2 in lmbda:
                    if path_has_link(failover_path, failed_link_2):
                        return None

                return failover_path

        return primary_path

    def test_active_flows_when_links_fail(self, out_reps):

        for i in xrange(len(out_reps)):
            print self.experiment_data["reps"][i]
            print self.experiment_data["reps"][i]['time_taken_per_active_flow_computation']

            lmbda = []

            # Pretend fail every link in the sequence
            for j, failed_link in enumerate(self.experiment_data["reps"][i]['failures']):
                lmbda.append(('s' + str(failed_link[1] + 1), 's' + str(failed_link[2] + 1)))

                num_active_synthesized_flows = 0
                num_active_analyzed_flows = 0

                # Check how many flows of the given set of flows still have Dijkstra paths
                for flow in self.experiment_data["flows"]:
                    s_host = "h" + str(flow[0] + 1) + "1"
                    t_host = "h" + str(flow[1] + 1) + "1"

                    active_analyzed_path = self.sdnsim_client.get_active_flow_path("s" + str(flow[0] + 1), 1,
                                                                                   "s" + str(flow[1] + 1), 1,
                                                                                   {"eth_type": 0x0800}, lmbda)

                    if active_analyzed_path:
                        num_active_analyzed_flows += 1

                    active_synthesized_path = self.get_active_synthesized_flow_when_links_fail(s_host,
                                                                                               t_host,
                                                                                               lmbda)
                    if active_synthesized_path:
                        num_active_synthesized_flows += 1

                    # if not self.same_paths(active_synthesized_path, active_analyzed_path):
                    #     print s_host, t_host, lmbda

                if num_active_synthesized_flows > num_active_analyzed_flows:
                    print "Total:", len(self.experiment_data["flows"]), \
                        "Synthesized:", num_active_synthesized_flows, \
                        "Analyzed:", num_active_analyzed_flows


def get_data_and_flow_specs(input_file):
    flow_specs = {"src_hosts": [], "dst_hosts": []}
    data = {"switches": None, "edges": [], "flows": [], "reps": []}

    rep_dict = None

    with open(input_file) as txt_file:

        for l in txt_file:
            if l.startswith("#"):
                continue

            if l.startswith("edge "):
                tokens = l.split()
                data["edges"].append([int(tokens[1]), int(tokens[2])])
                continue

            if l.startswith("flow "):
                tokens = l.split()
                data["flows"].append([int(tokens[1]), int(tokens[2])])
                continue

            if l.startswith("flow_epdf") or l.startswith("edge_epdf"):
                continue

            if l.startswith("replication "):
                if rep_dict:
                    data["reps"].append(rep_dict)

                rep_dict = {"replication": int(l.split()[1]), "failures": []}
                continue

            if l.startswith("at "):
                tokens = l.split()
                time = float(tokens[1])
                n1 = int(tokens[3].split(":")[0])
                n2 = int(tokens[3].split(":")[1])
                rep_dict["failures"].append([time, n1, n2])
                continue

            data["switches"] = int(l)

    data["reps"].append(rep_dict)

    for f in data["flows"]:
        src_host = "h" + str(f[0] + 1) + str(1)
        dst_host = "h" + str(f[1] + 1) + str(1)

        flow_specs["src_hosts"].append(src_host)
        flow_specs["dst_hosts"].append(dst_host)

    return data, flow_specs


def main():

    num_flows = 32
    for num_switches in [40, 50, 60, 70, 80, 90, 100, 110, 120]:

        input_file = "data/sdnsim_eval/" + str(num_switches) + '.' + str(num_flows) + '.txt'
        data, flow_specs = get_data_and_flow_specs(input_file)

        nc = NetworkConfiguration("ryu",
                                  "127.0.0.1",
                                  6633,
                                  "http://localhost:8080/",
                                  "admin",
                                  "admin",
                                  "wsc",
                                  {"num_switches": data["switches"],
                                   "edges": data["edges"],
                                   "num_hosts_per_switch": 1},
                                  conf_root="configurations/",
                                  synthesis_name="DijkstraSynthesis",
                                  synthesis_params={"apply_group_intents_immediately": True,
                                                    "k": 1})

        exp = WSC(nc, data, flow_specs, data['reps'])
        times_dict = exp.trigger(20)

        with open(str(num_switches) + '.' + str(num_flows) + '.json', "w") as json_file:
            json.dump(times_dict, json_file, indent=4)


def plot():
    num_flows = 32
    num_switches_list = [40, 50, 60, 70, 80, 90, 100, 110, 120]
    data_xticks = num_switches_list
    data_xtick_labels = [str(x) for x in data_xticks]

    x_min_factor = 0.9
    x_max_factor = 1.10


    data_dict = {
        "Initialization": {"mean": [], "sem": []},
        "Active Flow Computation": {"mean": [], "sem": []},
        "Sample Computation": {"mean": [], "sem": []},
        "Active Path Length": {"mean": [], "sem": []},
    }

    for num_switches in num_switches_list:

        with open("data/sdnsim_eval/" + str(num_switches) + '.' + str(num_flows) + '.json', "r") as json_file:
            times_dict = json.load(json_file)

            data_dict["Initialization"]["mean"].append(np.mean(times_dict["init_times"])/1000000000)
            data_dict["Initialization"]["sem"].append(ss.sem(times_dict["init_times"])/1000000000)

            data_dict["Active Flow Computation"]["mean"].append(np.mean(times_dict["active_flow_times"])/1000000000)
            data_dict["Active Flow Computation"]["sem"].append(ss.sem(times_dict["active_flow_times"])/1000000000)

            data_dict["Sample Computation"]["mean"].append(np.mean(times_dict["total_times"])/1000000000)
            data_dict["Sample Computation"]["sem"].append(ss.sem(times_dict["total_times"])/1000000000)

            data_dict["Active Path Length"]["mean"].append(np.median(times_dict["path_lengths"]))
            data_dict["Active Path Length"]["sem"].append(ss.sem(times_dict["path_lengths"]))

    y_min_factor = 0.01
    y_max_factor = 10

    f, (ax) = plt.subplots(1, 1,
                           sharex=True,
                           sharey=False,
                           figsize=(5.0, 4.0))

    ax.set_xlabel("Number of Switches", fontsize=10, labelpad=-0)
    ax.set_ylabel("Time(seconds)", fontsize=10, labelpad=0)
    ax.set_title("", fontsize=10)

    markers = ['*', '.', 'v', '+', 'd', 'o', '^', 'H', ',', 's', '*']
    marker_i = 0

    for line_data_key in ["Initialization",
                          "Active Flow Computation",
                          "Sample Computation"]:

        means = data_dict[line_data_key]["mean"]
        sems = data_dict[line_data_key]["sem"]

        ax.errorbar(x=num_switches_list,
                    y=means,
                    yerr=sems,
                    color="black",
                    marker=markers[marker_i],
                    markersize=7.0,
                    label=line_data_key,
                    ls='none')

        marker_i += 1

    ax.tick_params(axis='x', labelsize=10)
    ax.tick_params(axis='y', labelsize=10)

    low_xlim, high_xlim = ax.get_xlim()
    ax.set_xlim(xmax=(high_xlim) * x_max_factor)
    ax.set_xlim(xmin=(low_xlim) * x_min_factor)

    low_ylim, high_ylim = ax.get_ylim()
    ax.set_ylim(ymin=low_ylim * y_min_factor)
    ax.set_ylim(ymax=high_ylim * y_max_factor)

    ax.set_yscale("log")
    ax.set_ylim(ymin=0.0001)
    ax.set_ylim(ymax=100000)

    xa = ax.get_xaxis()
    xa.set_major_locator(MaxNLocator(integer=True))

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles,
              labels,
              shadow=True,
              fontsize=10,
              frameon=True,
              loc="upper right",
              ncol=1)

    plt.savefig("sdnsim_evaluation_1" + ".png", dpi=1000)
    plt.show()

    ####
    y_min_factor = 1
    y_max_factor = 1.1

    f, (ax) = plt.subplots(1, 1,
                           sharex=True,
                           sharey=False,
                           figsize=(5.0, 4.0))

    ax.set_xlabel("Number of Switches", fontsize=10, labelpad=-0)
    ax.set_ylabel("Time(seconds)", fontsize=10, labelpad=0)
    ax.set_title("", fontsize=10)

    markers = ['*', '.', 'v', '+', 'd', 'o', '^', 'H', ',', 's', '*']
    marker_i = 0

    for line_data_key in ["Active Path Length"]:

        means = data_dict[line_data_key]["mean"]
        sems = data_dict[line_data_key]["sem"]

        ax.errorbar(x=num_switches_list,
                    y=means,
                    yerr=sems,
                    color="black",
                    marker=markers[marker_i],
                    markersize=7.0,
                    label=line_data_key,
                    ls='none')

        marker_i += 1

    ax.tick_params(axis='x', labelsize=10)
    ax.tick_params(axis='y', labelsize=10)

    low_xlim, high_xlim = ax.get_xlim()
    ax.set_xlim(xmax=(high_xlim) * x_max_factor)
    ax.set_xlim(xmin=(low_xlim) * x_min_factor)

    low_ylim, high_ylim = ax.get_ylim()
    ax.set_ylim(ymin=low_ylim * y_min_factor)
    ax.set_ylim(ymax=high_ylim * y_max_factor)

    ax.set_yscale("linear")
    low_ylim, high_ylim = ax.get_ylim()
    ax.set_ylim(ymin=low_ylim*y_min_factor)
    ax.set_ylim(ymax=high_ylim*y_max_factor)

    xa = ax.get_xaxis()
    xa.set_major_locator(MaxNLocator(integer=True))

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles,
              labels,
              shadow=True,
              fontsize=10,
              frameon=True,
              loc="upper right",
              ncol=1)

    plt.savefig("sdnsim_evaluation_2" + ".png", dpi=1000)
    plt.show()


if __name__ == "__main__":
    #main()
    plot()
