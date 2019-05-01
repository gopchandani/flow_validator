import sys
import json
import argparse
import grpc
from rpc import flow_validator_pb2
from rpc import flow_validator_pb2_grpc
from experiment import Experiment
from experiments.network_configuration import NetworkConfiguration
from analysis.policy_statement import CONNECTIVITY_CONSTRAINT

__author__ = 'Rakesh Kumar'

sys.path.append("./")


class WSC(Experiment):

    def __init__(self, nc, experiment_data, flow_specs, reps):

        super(WSC, self).__init__("playground", 1)
        self.nc = nc
        self.rpc_links = self.init_rpc_links()
        self.experiment_data = experiment_data
        self.flow_specs = flow_specs
        self.reps = reps

        self.channel = None
        self.stub = None

    def flow_validator_initialize(self):
        rpc_ng = self.prepare_rpc_network_graph(self.flow_specs)

        try:
            init_info = self.stub.Initialize(rpc_ng)
            print "Initialize was successful, time taken:", init_info.time_taken/1000000000, "seconds."
        except grpc.RpcError as e:
            print "Call to Initialize failed:", e.details(), e.code().name, e.code().value

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
                link_failure_sequence.append(self.rpc_links["s" + str(f[1]+1)]["s" + str(f[2]+1)])

            reps.append(flow_validator_pb2.NumActiveFlowsRep(link_failure_sequence=link_failure_sequence,
                                                             num_active_flows=[]))

        nafp = flow_validator_pb2.NumActiveFlowsParams(flows=flows, reps=reps)

        try:
            nafi = self.stub.GetNumActiveFlowsAtFailureTimes(nafp)

            print "GetNumActiveFlowsAtFailureTimes was successful, time taken:", nafi.time_taken/1000000000, "seconds."

            for i in xrange(len(nafi.reps)):
                self.experiment_data["reps"][i]["num_active_flows"] = list(nafi.reps[i].num_active_flows)

        except grpc.RpcError as e:
            print "Call to GetNumActiveFlowsAtFailureTimes failed:", e.details(), e.code().name, e.code().value

    def flow_validator_get_active_flow_path(self):

        policy_match = dict()
        policy_match["eth_type"] = 0x0800

        flow = flow_validator_pb2.Flow(src_port=flow_validator_pb2.PolicyPort(switch_id="s3", port_num=1),
                                       dst_port=flow_validator_pb2.PolicyPort(switch_id="s25", port_num=1),
                                       policy_match=policy_match)

        lmbda = flow_validator_pb2.Lmbda(links=[self.rpc_links["s2"]["s1"]])

        nafp = flow_validator_pb2.ActivePathParams(flow=flow, lmbda=lmbda)

        try:
            api = self.stub.GetActiveFlowPath(nafp)
            print "Initialize was successful, time taken:", api.time_taken/1000000000, "seconds."
        except grpc.RpcError as e:
            print "Call to Initialize failed:", e.details(), e.code().name, e.code().value

    def trigger(self):
        self.channel = grpc.insecure_channel('localhost:50051')
        self.stub = flow_validator_pb2_grpc.FlowValidatorStub(self.channel)

        self.flow_validator_initialize()

        self.flow_validator_get_active_flow_path()

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

