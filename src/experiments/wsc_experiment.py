import sys
import json
import argparse
from experiment import Experiment
from experiments.network_configuration import NetworkConfiguration
from analysis.sdnsim_client import SDNSimClient
import networkx as nx

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

    def trigger(self):

        self.sdnsim_client.initialize_sdnsim()

        src_ports, dst_ports, policy_matches = [], [], []

        for i in xrange(len(self.flow_specs["src_hosts"])):
            src_h_obj = self.nc.ng.get_node_object(self.flow_specs["src_hosts"][i])
            dst_h_obj = self.nc.ng.get_node_object(self.flow_specs["dst_hosts"][i])

            src_ports.append((src_h_obj.sw.node_id, src_h_obj.switch_port.port_number))
            dst_ports.append((dst_h_obj.sw.node_id, dst_h_obj.switch_port.port_number))

            policy_matches.append({"eth_type": 0x0800})

            # self.nc.is_host_pair_pingable(self.nc.mininet_obj.get(src_h_obj.node_id),
            #                               self.nc.mininet_obj.get(dst_h_obj.node_id))

        out_reps = self.sdnsim_client.get_num_active_flows_when_links_fail(self.reps,
                                                                           src_ports, dst_ports, policy_matches)

        #self.test_active_flows_when_links_fail(self.reps)

        for i in xrange(len(out_reps)):
            self.experiment_data["reps"][i]["num_active_flows"] = list(out_reps[i].num_active_flows)

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", help="Input file")
    parser.add_argument("--output_file", help="Output file")
    args = parser.parse_args()

    flow_specs = {"src_hosts": [], "dst_hosts": []}

    with open(args.input_file) as json_file:
        data = json.load(json_file)
        num_switches = data["switches"]
        edges = data["edges"]
        reps = data['reps']

        for f in data["flows"]:
            src_host = "h" + str(f[0]+1) + str(1)
            dst_host = "h" + str(f[1]+1) + str(1)

            flow_specs["src_hosts"].append(src_host)
            flow_specs["dst_hosts"].append(dst_host)

    nc = NetworkConfiguration("ryu",
                              "127.0.0.1",
                              6633,
                              "http://localhost:8080/",
                              "admin",
                              "admin",
                              "wsc",
                              {"num_switches": num_switches,
                               "edges": edges,
                               "num_hosts_per_switch": 1},
                              conf_root="configurations/",
                              synthesis_name="DijkstraSynthesis",
                              synthesis_params={"apply_group_intents_immediately": True,
                                                "k": 1})

    exp = WSC(nc, data, flow_specs, reps)
    exp.trigger()

    with open(args.output_file, "w") as json_file:
        json.dump(exp.experiment_data, json_file, indent=4)


if __name__ == "__main__":
    main()

