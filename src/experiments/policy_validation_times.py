import sys
import json

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from collections import defaultdict

from timer import Timer
from experiment import Experiment
from network_configuration import NetworkConfiguration
from model.traffic import Traffic
from analysis.flow_validator import FlowValidator

__author__ = 'Rakesh Kumar'

sys.path.append("./")

from analysis.policy_statement import PolicyStatement, PolicyConstraint
from analysis.policy_statement import CONNECTIVITY_CONSTRAINT


class PolicyValidationTimes(Experiment):

    def __init__(self,
                 network_configurations,
                 k_values,
                 num_iterations,
                 optimizations_to_use):

        super(PolicyValidationTimes, self).__init__("substation_mixed_policy_validation_times", 1)

        self.network_configurations = network_configurations
        self.k_values = k_values
        self.num_iterations = num_iterations
        self.optimizations_to_use = optimizations_to_use

        self.data = {
            "validation_time": defaultdict(defaultdict),
        }

    def construct_policy_statements(self, nc, k):

        all_host_ports_zone = []
        for host_obj in nc.ng.get_host_obj_iter():
            all_host_ports_zone.append(host_obj.switch_port)

        t = Traffic(init_wildcard=True)
        t.set_field("ethernet_type", 0x0800)
        t.set_field("has_vlan_tag", 0)
        c = [PolicyConstraint(CONNECTIVITY_CONSTRAINT, None)]
        policy_statements = [PolicyStatement(nc.ng, all_host_ports_zone, all_host_ports_zone, t, c, k)]

        return policy_statements

    def trigger(self):

        for nc in self.network_configurations:

            print "Configuration:", nc

            fv = FlowValidator(nc.ng)
            fv.init_network_port_graph()

            print "Initialized analysis."

            for k in self.k_values:

                policy_statements = self.construct_policy_statements(nc, k)

                sL = str(len(list(nc.ng.get_switch_link_data())))

                for optimization_to_use in self.optimizations_to_use:

                    self.data["validation_time"]["k: " + str(k) + ", |L|: " + sL][optimization_to_use] = []

                    for i in range(self.num_iterations):

                        with Timer(verbose=True) as t:
                            violations = fv.init_policy_validation(policy_statements, optimization_to_use)

                        print "Total violations:", len(violations)

                        print "Does the network configuration satisfy the given policy:", (len(violations) == 0)

                        self.data["validation_time"]["k: " + str(k) + ", |L|: " + sL][optimization_to_use].append(t.secs)

                        self.dump_data()

    def plot_lines_with_error_bars(self,
                                   ax,
                                   data_key,
                                   x_label,
                                   y_label,
                                   subplot_title,
                                   y_scale,
                                   x_min_factor=1.0,
                                   x_max_factor=1.05,
                                   y_min_factor=0.1,
                                   y_max_factor=1.5,
                                   xticks=None,
                                   xtick_labels=None,
                                   yticks=None,
                                   ytick_labels=None):

        ax.set_xlabel(x_label, fontsize=11, labelpad=-0)
        ax.set_ylabel(y_label, fontsize=11, labelpad=0)
        ax.set_title(subplot_title, fontsize=12)

        markers = ['.', 'x', '^', 'v', '*', '+', 'H', 's']
        marker_i = 0

        for line_data_key in sorted(self.data[data_key].keys()):

            style = None

            if line_data_key.find("0") == 3:
                style = "dotted"
            elif line_data_key.find("1") == 3:
                style = "dashed"
            elif line_data_key.find("2") == 3:
                style = "dashdot"
            elif line_data_key.find("3") == 3:
                style = "solid"

            data_vals = self.data[data_key][line_data_key]

            x, mean, sem = self.prepare_matplotlib_data(data_vals)

            ax.errorbar(x,
                        mean,
                        sem,
                        color="black",
                        marker=markers[marker_i],
                        markersize=7.0,
                        label=line_data_key,
                        ls="none")

            marker_i += 1

        ax.tick_params(axis='x', labelsize=11)
        ax.tick_params(axis='y', labelsize=11)

        low_xlim, high_xlim = ax.get_xlim()
        ax.set_xlim(xmax=(high_xlim) * x_max_factor)
        ax.set_xlim(xmin=(low_xlim) * x_min_factor)

        if y_scale == "linear":
            low_ylim, high_ylim = ax.get_ylim()
            ax.set_ylim(ymin=low_ylim*y_min_factor)
            ax.set_ylim(ymax=high_ylim*y_max_factor)
        elif y_scale == "log":
            ax.set_ylim(ymin=2)
            ax.set_ylim(ymax=100000)

        ax.set_yscale(y_scale)

        xa = ax.get_xaxis()
        xa.set_major_locator(MaxNLocator(integer=True))

        if xticks:
            ax.set_xticks(xticks)

        if xtick_labels:
            ax.set_xticklabels(xtick_labels)

        if yticks:
            ax.set_yticks(yticks)

        if ytick_labels:
            ax.set_yticklabels(ytick_labels)

    def plot_data(self):

        f, (ax1) = plt.subplots(1, 1, sharex=True, sharey=False, figsize=(5.5, 4.0))

        self.plot_bar_error_bars(ax1,
                                 "validation_time",
                                 x_label="",
                                 y_label="Time (seconds)",
                                 bar_width=0.2,
                                 y_max_factor=1.05)

        # Shrink current axis's height by 25% on the bottom
        box = ax1.get_position()
        ax1.set_position([box.x0, box.y0 + box.height * 0.3, box.width, box.height * 0.7])

        handles, labels = ax1.get_legend_handles_labels()
        handles = [handles[0], handles[1]]
        labels = ["With Preemption", "Without Preemption"]

        plt.legend(handles, labels, loc='upper center',
                   shadow=True, ncol=2, fontsize=10, bbox_to_anchor=[0.5, -0.25],
                   frameon=True, fancybox=True, columnspacing=2.5, markerscale=1.0)

        xlabels = ax1.get_xticklabels()
        plt.setp(xlabels, rotation=15, fontsize=10)

        ylabels = ax1.get_yticklabels()
        plt.setp(ylabels, rotation=0, fontsize=10)

        plt.savefig("plots/" + self.experiment_tag + "_policy_validation_times" + ".png", dpi=1000)
        plt.show()

    def load_data_merge_iterations(self, filename_list):

        '''
        :param filename_list: List of files with exact same network configurations in them
        :return: merged data
        '''

        merged_data = None

        for filename in filename_list:

            print "Reading file:", filename

            with open(filename, "r") as infile:
                this_data = json.load(infile)

            if merged_data:
                for ds in merged_data:
                    for case in merged_data[ds]:
                        for num_conns in merged_data[ds][case]:
                            try:
                                merged_data[ds][case][num_conns].extend(this_data[ds][case][num_conns])
                            except KeyError:
                                print filename, ds, case, num_conns, "not found."
            else:
                merged_data = this_data

        return merged_data


def prepare_network_configurations(num_switches_in_clique_list, num_hosts_per_switch_list, num_per_switch_links_list):
    nc_list = []

    for nsc in num_switches_in_clique_list:

        for hps in num_hosts_per_switch_list:

            for psl in num_per_switch_links_list:

                nc = NetworkConfiguration("ryu",
                                          "127.0.0.1",
                                          6633,
                                          "http://localhost:8080/",
                                          "admin",
                                          "admin",
                                          "cliquetopo",
                                          {"num_switches": nsc,
                                           "num_hosts_per_switch": hps,
                                           "per_switch_links": psl},
                                          conf_root="configurations/",
                                          synthesis_name="AboresceneSynthesis",
                                          synthesis_params={"apply_group_intents_immediately": True})

                nc.setup_network_graph(mininet_setup_gap=10, synthesis_setup_gap=10)

                nc_list.append(nc)

    return nc_list


def main():

    num_iterations = 1
    #optimizations_to_use = ["Without Preemption", "With Preemption"]
    optimizations_to_use = ["With Preemption"]
    # optimizations_to_use = ["Without Preemption"]

    k_values = [1, 2]#[1, 2, 3]
    num_switches_in_clique_list = [4]
    num_per_switch_links_list = [2]#[2, 3]
    num_hosts_per_switch_list = [1]

    network_configurations = prepare_network_configurations(num_switches_in_clique_list,
                                                            num_hosts_per_switch_list,
                                                            num_per_switch_links_list)

    exp = PolicyValidationTimes(network_configurations, k_values, num_iterations, optimizations_to_use)

    exp.trigger()
    # exp.dump_data()
    # exp.plot_data()

if __name__ == "__main__":
    main()
