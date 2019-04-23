import json
import pickle
import time
import random
import math
import numpy as np
import scipy.stats as ss
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from pprint import pprint
from collections import defaultdict
from model.traffic import Traffic
from timer import Timer
from rpc import flow_validator_pb2
from rpc import flow_validator_pb2_grpc

from netaddr import IPNetwork
from collections import defaultdict

__author__ = 'Rakesh Kumar'


class Experiment(object):

    def __init__(self,
                 experiment_name,
                 num_iterations):

        self.experiment_tag = experiment_name + "_" + str(num_iterations) + "_iterations_" + time.strftime("%Y%m%d_%H%M%S")
        self.num_iterations = num_iterations

        self.data = {}

    def perform_incremental_times_experiment(self, fv, link_fraction_to_sample):

        all_links = list(fv.network_graph.get_switch_link_data())
        num_links_to_sample = int(math.ceil(len(all_links) * link_fraction_to_sample))

        incremental_times = []

        for i in range(num_links_to_sample):

            sampled_ld = random.choice(all_links)

            print "Failing:", sampled_ld
            with Timer(verbose=True) as t:
                fv.port_graph.remove_node_graph_link(sampled_ld.forward_link[0], sampled_ld.forward_link[1])
            incremental_times.append(t.secs)
            print incremental_times

            print "Restoring:", sampled_ld
            with Timer(verbose=True) as t:
                fv.port_graph.add_node_graph_link(sampled_ld.forward_link[0], sampled_ld.forward_link[1], updating=True)
            incremental_times.append(t.secs)
            print incremental_times

        return np.mean(incremental_times)

    def dump_data(self):
        print "Dumping data:"
        pprint(self.data)
        filename = "data/" + self.experiment_tag + ".json"
        print "Writing to file:", filename

        with open(filename, "w") as outfile:
            json.dump(self.data, outfile)

    def dump_violations(self, violations):
        print "Dumping violations:"
        filename = "data/" + self.experiment_tag + "_violations.pickle"
        print "Writing violations to file:", filename
        with open(filename, "w") as outfile:
            pickle.dump(violations, outfile)

    def load_data(self, filename):

        print "Reading file:", filename

        with open(filename, "r") as infile:
            self.data = json.load(infile)

        pprint(self.data)

        return self.data

    def prepare_matplotlib_data(self, data_dict):

        if type(data_dict.keys()[0]) == int:
            x = sorted(data_dict.keys(), key=int)
        elif type(data_dict.keys()[0]) == str or type(data_dict.keys()[0]) == unicode:
            x = sorted(data_dict.keys(), key=int)

        data_means = []
        data_sems = []

        for p in x:
            mean = np.mean(data_dict[p])
            sem = ss.sem(data_dict[p])
            data_means.append(mean)
            data_sems.append(sem)

        return x, data_means, data_sems

    def get_data_min_max(self, data_dict):

        data_min = None
        data_max = None

        for p in data_dict:
            p_min = min(data_dict[p])

            if data_min:
                if p_min < data_min:
                    data_min = p_min
            else:
                data_min = p_min

            p_max = max(data_dict[p])
            if data_max:
                if p_max > data_max:
                    data_max = p_max
            else:
                data_max = p_max

        return data_min, data_max

    def plot_bar_error_bars(self, ax, data_key, x_label, y_label, title="",
                            bar_width=0.35, opacity=0.4, error_config={'ecolor': '0.3'},
                            y_scale="linear", y_min_factor=0.1, y_max_factor=1.5):

        index = np.arange(len(self.data[data_key].keys()))

        categories_mean_dict = defaultdict(list)
        categories_se_dict = defaultdict(list)

        for line_data_group in sorted(self.data[data_key].keys()):
            data_vals = self.data[data_key][line_data_group]
            categories, mean, sem = self.prepare_matplotlib_data(data_vals)

            for i in xrange(len(categories)):
                categories_mean_dict[categories[i]].append(mean[i])
                categories_se_dict[categories[i]].append(sem[i])

        categories_hatches = ['/', '', 'o', 'O', '*', '.', '-', '+', 'x', '\\']
        for i in range(len(categories)):
            c = categories[i]
            rects = ax.bar(index + bar_width * i, categories_mean_dict[c],
                           bar_width,
                           alpha=opacity + 0.10,
                           color='black',
                           hatch=categories_hatches[i],
                           yerr=categories_se_dict[c],
                           error_kw=error_config,
                           label=c)

        if y_scale == "linear":
            low_ylim, high_ylim = ax.get_ylim()
            ax.set_ylim(ymin=low_ylim*y_min_factor)
            ax.set_ylim(ymax=high_ylim*y_max_factor)
        elif y_scale == "log":
            ax.set_ylim(ymin=1)
            ax.set_ylim(ymax=10000)

        ax.set_yscale(y_scale)

        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.title(title)
        plt.xticks(index + bar_width, tuple(sorted(self.data[data_key].keys())))

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

        ax.set_xlabel(x_label, fontsize=10, labelpad=-0)
        ax.set_ylabel(y_label, fontsize=10, labelpad=0)
        ax.set_title(subplot_title, fontsize=10)

        markers = ['*', '.', 'v', '+', 'd', 'o', '^', 'H', ',', 's', '*']
        marker_i = 0

        for line_data_key in sorted(self.data[data_key].keys()):

            data_vals = self.data[data_key][line_data_key]

            x, mean, sem = self.prepare_matplotlib_data(data_vals)

            ax.errorbar(x, mean, sem, color="black",
                        marker=markers[marker_i], markersize=7.0, label=line_data_key, ls='none')

            marker_i += 1

        ax.tick_params(axis='x', labelsize=10)
        ax.tick_params(axis='y', labelsize=10)

        low_xlim, high_xlim = ax.get_xlim()
        ax.set_xlim(xmax=(high_xlim) * x_max_factor)
        ax.set_xlim(xmin=(low_xlim) * x_min_factor)

        if y_scale == "linear":
            low_ylim, high_ylim = ax.get_ylim()
            ax.set_ylim(ymin=low_ylim*y_min_factor)
            ax.set_ylim(ymax=high_ylim*y_max_factor)
        elif y_scale == "log":
            ax.set_ylim(ymin=1)
            ax.set_ylim(ymax=10000)

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

    def prepare_rpc_actions(self, actions):
        rpc_actions = []

        for action in actions:

            rpc_action = flow_validator_pb2.Action(type=action["type"])

            if action["type"] == "SET_FIELD" and "field" in action and "value" in action:
                rpc_action.modified_field = action["field"]
                rpc_action.modified_value = int(action["value"])

            if action["type"] == "GROUP" and "group_id" in action:
                rpc_action.group_id = int(action["group_id"])

            if action["type"] == "OUTPUT" and "port" in action:
                rpc_action.output_port_num = action["port"]

            rpc_actions.append(rpc_action)

        return rpc_actions

    def prepare_rpc_field_value(self, field_name, field_value):
        field_val = None
        has_vlan_tag = False

        if field_name == "in_port":
            try:
                field_val = int(field_value)
            except ValueError:
                parsed_in_port = field_value.split(":")[2]
                field_val = int(parsed_in_port)

        elif field_name == "eth_type":
            field_val = int(field_value)

        elif field_name == "eth_src":
            mac_int = int(field_value.replace(":", ""), 16)
            field_val = mac_int

        elif field_name == "eth_dst":
            mac_int = int(field_value.replace(":", ""), 16)
            field_val = mac_int

        # TODO: Add graceful handling of IP addresses
        elif field_name == "nw_src":
            field_val = IPNetwork(field_value)
        elif field_name == "nw_dst":
            field_val = IPNetwork(field_value)

        elif field_name == "ip_proto":
            field_val = int(field_value)
        elif field_name == "tcp_dst":

            if field_value == 6:
                field_val = int(field_value)
            else:
                field_val = sys.maxsize

        elif field_name == "tcp_src":

            if field_value == 6:
                field_val = int(field_value)
            else:
                field_val = sys.maxsize

        elif field_name == "udp_dst":

            if field_value == 17:
                field_val = int(field_value)
            else:
                field_val = sys.maxsize

        elif field_name == "udp_src":

            if field_value == 17:
                field_val = int(field_value)
            else:
                field_val = sys.maxsize

        elif field_name == "vlan_vid":

            if field_value == "0x1000/0x1000":
                field_val = 0x1000
            else:
                field_val = 0x1000 + int(field_value)

        if not isinstance(field_val, IPNetwork):
            return flow_validator_pb2.FlowRuleMatchFieldVal(value_start=field_val, value_end=field_val)
        else:
            return flow_validator_pb2.FlowRuleMatchFieldVal(value_start=field_val.first, value_end=field_val.last)

    def prepare_rpc_match(self, match):

        match_fields = {}
        for field_name, field_value in match.items():
            match_fields[field_name] = self.prepare_rpc_field_value(field_name, field_value)

        return match_fields

    def prepare_rpc_instructions(self, instructions):
        rpc_instructions = []

        for instruction in instructions:

            if instruction["type"] == "GOTO_TABLE":
                rpc_instruction = flow_validator_pb2.Instruction(
                    type=instruction["type"],
                    go_to_table_num=instruction["table_id"])
            else:
                rpc_instruction = flow_validator_pb2.Instruction(
                    type=instruction["type"],
                    actions=self.prepare_rpc_actions(instruction["actions"]))

            rpc_instructions.append(rpc_instruction)

        return rpc_instructions

    def prepare_rpc_switches(self):
        switches = self.nc.get_switches()

        rpc_switches = []

        for sw_id, switch in switches.items():

            rpc_ports = []
            for port in switch["ports"]:

                try:
                    port_no = int(port["port_no"])
                except:
                    continue

                rpc_port = flow_validator_pb2.Port(port_num=port_no, hw_addr=port["hw_addr"])
                rpc_ports.append(rpc_port)

            rpc_groups = []
            for group in switch["groups"]:

                rpc_buckets = []
                for bucket in group["buckets"]:
                    rpc_actions = self.prepare_rpc_actions(bucket["actions"])
                    rpc_bucket = flow_validator_pb2.Bucket(watch_port_num=bucket["watch_port"],
                                                           weight=bucket["weight"],
                                                           actions=rpc_actions)
                    rpc_buckets.append(rpc_bucket)

                rpc_group = flow_validator_pb2.Group(id=group["group_id"], type=group["type"], buckets=rpc_buckets)
                rpc_groups.append(rpc_group)

            rpc_flow_tables = []
            for table_num, flow_table in switch["flow_tables"].items():

                rpc_flow_rules = []
                for flow_rule in flow_table:
                    rpc_flow_rule = flow_validator_pb2.FlowRule(
                        priority=int(flow_rule["priority"]),
                        flow_rule_match=self.prepare_rpc_match(flow_rule["match"]),
                        instructions=self.prepare_rpc_instructions(flow_rule["instructions"]))

                    rpc_flow_rules.append(rpc_flow_rule)

                rpc_flow_table = flow_validator_pb2.FlowTable(table_num=int(table_num), flow_rules=rpc_flow_rules)
                rpc_flow_tables.append(rpc_flow_table)

            rpc_switch = flow_validator_pb2.Switch(flow_tables = rpc_flow_tables,
                                                   group_table=rpc_groups,
                                                   ports=rpc_ports,
                                                   switch_id='s' + str(sw_id))

            rpc_switches.append(rpc_switch)

        return rpc_switches

    def prepare_rpc_hosts(self):
        hosts = self.nc.get_host_nodes()

        rpc_hosts = []

        for host_switch in hosts.values():
            for host in host_switch:
                rpc_host = flow_validator_pb2.Host(host_IP=host["host_IP"],
                                                   host_MAC=host["host_MAC"],
                                                   host_name=host["host_name"],
                                                   host_switch_id=host["host_switch_id"])
                rpc_hosts.append(rpc_host)

        return rpc_hosts

    def prepare_rpc_link(self, src_node, dst_node):

        src_node_port = 0
        dst_node_port = 0

        rpc_link = flow_validator_pb2.Link(src_node=src_node,
                                           src_port_num=int(src_node_port),
                                           dst_node=dst_node,
                                           dst_port_num=int(dst_node_port))

        return rpc_link

    def init_rpc_links(self):
        links = self.nc.get_all_links()

        rpc_links = defaultdict(dict)

        for src_node in links:
            for src_node_port in links[src_node]:
                dst_list = links[src_node][src_node_port]
                dst_node = dst_list[0]
                dst_node_port = dst_list[1]

                rpc_link = flow_validator_pb2.Link(src_node=src_node,
                                                   src_port_num=int(src_node_port),
                                                   dst_node=dst_node,
                                                   dst_port_num=int(dst_node_port))

                rpc_links[src_node][dst_node] = rpc_link

        return rpc_links

    def prepare_rpc_links(self):
        rpc_links_list = []

        for src_node in self.rpc_links:
            for dst_node in self.rpc_links[src_node]:
                rpc_links_list.append(self.rpc_links[src_node][dst_node])

        return rpc_links_list

    def prepare_rpc_network_graph(self, flow_specs=None):

        ng = self.nc.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1, flow_specs=flow_specs)

        rpc_switches = self.prepare_rpc_switches()
        rpc_hosts = self.prepare_rpc_hosts()
        rpc_links = self.prepare_rpc_links()

        rpc_ng = flow_validator_pb2.NetworkGraph(controller="grpc",
                                                 switches=rpc_switches, hosts=rpc_hosts, links=rpc_links)

        return rpc_ng
