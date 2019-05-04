import sys
import json
import argparse
import grpc
from rpc import flow_validator_pb2
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

    def get_rpc_flows(self, src_ports, dst_ports):

        policy_match = dict()
        policy_match["eth_type"] = 0x0800

        flows = []

        for i in xrange(len(src_ports)):
            flows.append(flow_validator_pb2.Flow(
                src_port=flow_validator_pb2.PolicyPort(switch_id=src_ports[i][0], port_num=src_ports[i][1]),
                dst_port=flow_validator_pb2.PolicyPort(switch_id=dst_ports[i][0], port_num=dst_ports[i][1]),
                policy_match=policy_match))

        return flows

    def flow_validator_get_num_active_flows_at_failure_times(self):

        src_ports, dst_ports = [], []

        for i in xrange(len(self.flow_specs["src_hosts"])):
            src_h_obj = self.nc.ng.get_node_object(self.flow_specs["src_hosts"][i])
            dst_h_obj = self.nc.ng.get_node_object(self.flow_specs["dst_hosts"][i])

            src_ports.append((src_h_obj.sw.node_id, src_h_obj.switch_port.port_number))
            dst_ports.append((dst_h_obj.sw.node_id, dst_h_obj.switch_port.port_number))

            # self.nc.is_host_pair_pingable(self.nc.mininet_obj.get(src_h_obj.node_id),
            #                               self.nc.mininet_obj.get(dst_h_obj.node_id))

        flows = self.get_rpc_flows(src_ports, dst_ports)

        reps = []
        for rep in self.reps:
            link_failure_sequence = []
            for f in rep['failures']:
                link_failure_sequence.append(self.sdnsim_client.rpc_links["s" + str(f[1]+1)]["s" + str(f[2]+1)])

            reps.append(flow_validator_pb2.NumActiveFlowsRep(link_failure_sequence=link_failure_sequence,
                                                             num_active_flows=[]))

        nafp = flow_validator_pb2.NumActiveFlowsParams(flows=flows, reps=reps)

        try:
            nafi = self.sdnsim_client.stub.GetNumActiveFlowsAtFailureTimes(nafp)

            print "GetNumActiveFlowsAtFailureTimes was successful, time taken:", nafi.time_taken/1000000000, "seconds."

            for i in xrange(len(nafi.reps)):
                self.experiment_data["reps"][i]["num_active_flows"] = list(nafi.reps[i].num_active_flows)

        except grpc.RpcError as e:
            print "Call to GetNumActiveFlowsAtFailureTimes failed:", e.details(), e.code().name, e.code().value

    def trigger(self):

        self.sdnsim_client.initialize_sdnsim()

        # self.flow_validator_get_time_to_failure()

        # self.flow_validator_get_num_active_flows_at_failure_times()


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

