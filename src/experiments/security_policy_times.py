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
from analysis.policy_statement import CONNECTIVITY_CONSTRAINT, ISOLATION_CONSTRAINT


class SecurityPolicyTimes(Experiment):

    def __init__(self,
                 nc_list,
                 num_iterations):

        super(SecurityPolicyTimes, self).__init__("security_policy_times", 1)

        self.nc_list = nc_list
        self.num_iterations = num_iterations

        self.data = {
            "initialization_time": defaultdict(defaultdict),
            "validation_time": defaultdict(defaultdict)
        }

    def construct_policy_statements(self, nc):
        statements = []
        enclave_zones_traffic_tuples = []
        control_zone = []
        non_control_zone = []
        control_vlan_id = 255

        all_switches = sorted(list(nc.ng.get_switches()), key=lambda x: int(x.node_id[1:]))
        for sw in all_switches[0:len(all_switches) - 1]:

            enclave_zone = []
            for port_num in sw.host_ports:
                enclave_zone.append(sw.ports[port_num])

                if port_num == 1:
                    control_zone.append(sw.ports[port_num])
                else:
                    non_control_zone.append(sw.ports[port_num])

            enclave_specific_traffic = Traffic(init_wildcard=True)
            enclave_specific_traffic.set_field("ethernet_type", 0x0800)
            enclave_specific_traffic.set_field("vlan_id", int(sw.node_id[1:]) + 0x1000)
            enclave_specific_traffic.set_field("has_vlan_tag", 1)

            enclave_zones_traffic_tuples.append((enclave_zone, enclave_specific_traffic))

        for src_enclave_zone, src_enclave_specific_traffic in enclave_zones_traffic_tuples:
            for dst_enclave_zone, dst_enclave_specific_traffic in enclave_zones_traffic_tuples:
                if src_enclave_zone == dst_enclave_zone:

                    enclave_constraints = [PolicyConstraint(CONNECTIVITY_CONSTRAINT, None)]

                    enclave_statement = PolicyStatement(nc.ng,
                                                        src_enclave_zone,
                                                        dst_enclave_zone,
                                                        src_enclave_specific_traffic,
                                                        enclave_constraints, 0)

                    statements.append(enclave_statement)
                else:
                    enclave_constraints = [PolicyConstraint(ISOLATION_CONSTRAINT, None)]

                    enclave_statement = PolicyStatement(nc.ng,
                                                        src_enclave_zone,
                                                        dst_enclave_zone,
                                                        src_enclave_specific_traffic,
                                                        enclave_constraints, 0)

                    statements.append(enclave_statement)

        control_switch = all_switches[len(all_switches) - 1]
        control_zone.append(nc.ng.get_node_object("h" + control_switch.node_id[1:] + "1").switch_port)

        control_enclave_specific_traffic = Traffic(init_wildcard=True)
        control_enclave_specific_traffic.set_field("ethernet_type", 0x0800)
        control_enclave_specific_traffic.set_field("vlan_id", control_vlan_id + 0x1000)
        control_enclave_specific_traffic.set_field("has_vlan_tag", 1)

        enclave_constraints = [PolicyConstraint(CONNECTIVITY_CONSTRAINT, None)]
        enclave_statement = PolicyStatement(nc.ng,
                                            control_zone,
                                            control_zone,
                                            control_enclave_specific_traffic,
                                            enclave_constraints, 0)
        statements.append(enclave_statement)

        enclave_constraints = [PolicyConstraint(ISOLATION_CONSTRAINT, None)]
        enclave_statement = PolicyStatement(nc.ng,
                                            control_zone,
                                            non_control_zone,
                                            control_enclave_specific_traffic,
                                            enclave_constraints, 0)
        statements.append(enclave_statement)

        enclave_constraints = [PolicyConstraint(ISOLATION_CONSTRAINT, None)]
        enclave_statement = PolicyStatement(nc.ng,
                                            non_control_zone,
                                            control_zone,
                                            control_enclave_specific_traffic,
                                            enclave_constraints, 0)
        statements.append(enclave_statement)

        return statements

    def trigger(self):

        for nc in self.nc_list:

            with Timer(verbose=True) as t:
                fv = FlowValidator(nc.ng)
                fv.init_network_port_graph()

            policy_statements = self.construct_policy_statements(nc)
            policy_len_str = "# Policy Statements:" + str(len(policy_statements))

            print "Total statements:", len(policy_statements)

            self.data["initialization_time"][policy_len_str][nc.topo_params["nHostsPerSwitch"]] = []
            self.data["validation_time"][policy_len_str][nc.topo_params["nHostsPerSwitch"]] = []

            self.data["initialization_time"][policy_len_str][nc.topo_params["nHostsPerSwitch"]].append(t.secs)
            self.dump_data()

            for i in range(self.num_iterations):
                with Timer(verbose=True) as t:
                    violations = fv.validate_policy(policy_statements)

                self.data["validation_time"][policy_len_str][nc.topo_params["nHostsPerSwitch"]].append(t.secs)
                self.dump_data()
                print "Total violations:", len(violations)

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

            style = "solid"

            # if line_data_key.find("0") == 3:
            #     style = "dotted"
            # elif line_data_key.find("1") == 3:
            #     style = "dashed"
            # elif line_data_key.find("2") == 3:
            #     style = "dashdot"
            # elif line_data_key.find("3") == 3:
            #     style = "solid"

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

        f, (ax1) = plt.subplots(1, 1, sharex=True, sharey=False, figsize=(5.0, 4.0))

        data_xtick_labels = self.data["validation_time"]["# Policy Statements:12"].keys()
        data_xticks = [int(x) for x in data_xtick_labels]

        self.plot_lines_with_error_bars(ax1,
                                        "validation_time",
                                        "Number of hosts per enclave",
                                        "Time (seconds)",
                                        "",
                                        y_scale='linear',
                                        x_min_factor=0.75,
                                        x_max_factor=1.1,
                                        y_min_factor=0.9,
                                        y_max_factor=1,
                                        xticks=data_xticks,
                                        xtick_labels=data_xtick_labels)

        xlabels = ax1.get_xticklabels()
        plt.setp(xlabels, rotation=0, fontsize=10)

        # Shrink current axis's height by 25% on the bottom
        box = ax1.get_position()
        ax1.set_position([box.x0, box.y0 + box.height * 0.3, box.width, box.height * 0.7])
        handles, labels = ax1.get_legend_handles_labels()

        handles = [handles[0], handles[4], handles[5], handles[1], handles[2], handles[3]]
        labels = [labels[0], labels[4], labels[5], labels[1], labels[2], labels[3]]

        ax1.legend(handles, labels, shadow=True, fontsize=10, loc='upper center', ncol=2, markerscale=1.0,
                   frameon=True, fancybox=True, columnspacing=0.5, bbox_to_anchor=[0.5, -0.25])

        plt.savefig("plots/" + self.experiment_tag + "_substation_mixed_policy_validation_times" + ".png", dpi=1000)
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
                        for hps in merged_data[ds][case]:
                            try:
                                merged_data[ds][case][hps].extend(this_data[ds][case][hps])
                            except KeyError:
                                print filename, ds, case, "not found."
            else:
                merged_data = this_data

        return merged_data

    def load_data_merge_num_statements(self, filename_list):

        merged_data = None

        for filename in filename_list:

            print "Reading file:", filename

            with open(filename, "r") as infile:
                this_data = json.load(infile)

            if merged_data:
                for ds in merged_data:
                    merged_data[ds].update(this_data[ds])
            else:
                merged_data = this_data

        return merged_data

    def load_data_merge_nhps(self, filename_list, prev_merged_data=None):
        merged_data = prev_merged_data

        for filename in filename_list:

            print "Reading file:", filename

            with open(filename, "r") as infile:
                this_data = json.load(infile)

            if merged_data:
                for ds in merged_data:
                    for nps in merged_data[ds]:

                        if nps not in this_data[ds]:
                            continue

                        merged_data[ds][nps].update(this_data[ds][nps])
            else:
                merged_data = this_data

        return merged_data


def prepare_network_configurations(num_grids_list, num_hosts_per_switch_list):

    nc_list = []
    num_switches_per_grid = 3

    for num_grids in num_grids_list:

        for num_hosts_per_switch in num_hosts_per_switch_list:

            ip_str = "172.17.0.2"
            port_str = "8181"

            nc = NetworkConfiguration("onos",
                                      ip_str,
                                      int(port_str),
                                      "http://" + ip_str + ":" + port_str + "/onos/v1/",
                                      "karaf",
                                      "karaf",
                                      "microgrid_topo",
                                      {"num_switches": 1 + num_grids * num_switches_per_grid,
                                       "nGrids": num_grids,
                                       "nSwitchesPerGrid": num_switches_per_grid,
                                       "nHostsPerSwitch": num_hosts_per_switch},
                                      conf_root="configurations/",
                                      synthesis_name=None,
                                      synthesis_params=None)

            nc.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

            nc_list.append(nc)

    return nc_list


def main():

    num_iterations = 10
    num_grids_list = [6]
    num_hosts_per_switch_list = [12]
    nc_list = prepare_network_configurations(num_grids_list, num_hosts_per_switch_list)
    exp = SecurityPolicyTimes(nc_list, num_iterations)

    # exp.trigger()
    # exp.dump_data()

    # exp.load_data("data/security_policy_times_1_iterations_20161226_114304.json")
    # exp.plot_data()

    exp.data = exp.load_data_merge_num_statements(
        ["data/security_policy_times_1_iterations_20161226_114304.json",
         "data/security_policy_times_1_iterations_20161226_125827.json",
         "data/security_policy_times_1_iterations_20161226_162225.json",
         "data/security_policy_times_1_iterations_20161228_172723.json"
         ])

    exp.data = exp.load_data_merge_nhps(["data/security_policy_times_1_iterations_20161229_092125.json"],
                                        prev_merged_data=exp.data)

    exp.data = exp.load_data_merge_nhps(["data/security_policy_times_1_iterations_20161230_101406.json"],
                                        prev_merged_data=exp.data)


    exp.plot_data()

if __name__ == "__main__":
    main()
