import sys
import json
import argparse
from experiment import Experiment
from experiments.network_configuration import NetworkConfiguration
from analysis.sdnsim_client import SDNSimClient

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

        print len(out_reps)

        for i in xrange(len(out_reps)):
            self.experiment_data["reps"][i]["num_active_flows"] = list(out_reps[i].num_active_flows)


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

