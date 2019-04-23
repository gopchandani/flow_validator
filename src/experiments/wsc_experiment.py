import sys
import json
import grpc
from rpc import flow_validator_pb2
from rpc import flow_validator_pb2_grpc
from experiment import Experiment
from experiments.network_configuration import NetworkConfiguration
from analysis.policy_statement import CONNECTIVITY_CONSTRAINT

__author__ = 'Rakesh Kumar'

sys.path.append("./")


class WSC(Experiment):

    def __init__(self, nc, input, flow_specs, reps):

        super(WSC, self).__init__("playground", 1)
        self.nc = nc
        self.rpc_links = self.init_rpc_links()
        self.input = input
        self.flow_specs = flow_specs
        self.reps = reps

        self.channel = None
        self.stub = None

    def flow_validator_initialize(self):
        rpc_ng = self.prepare_rpc_network_graph(self.flow_specs)
        init_info = self.stub.Initialize(rpc_ng)

        if init_info.successful:
            print "Server said initialization was successful, time taken:", init_info.time_taken
        else:
            print "Server said initialization was not successful"

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

    def flow_validator_get_time_to_failure(self):

        num_iterations = 1000
        link_failure_rate = 1.0
        src_ports = [('s1', 1)]
        dst_ports = [('s4', 1)]

        flows = self.get_rpc_flows(src_ports, dst_ports)

        mcp = flow_validator_pb2.MonteCarloParams(num_iterations=num_iterations,
                                                  link_failure_rate=link_failure_rate,
                                                  flows=flows,
                                                  seed=42)

        ttf = self.stub.GetTimeToDisconnect(mcp)

        print "Mean TTF: ", ttf.mean
        print "SD TTF:", ttf.sd
        print "Time taken:", ttf.time_taken

    def flow_validator_get_num_active_flows_at_failure_times(self):

        src_ports, dst_ports = [], []

        for i in xrange(len(self.flow_specs["src_hosts"])):
            src_h_obj = self.nc.ng.get_node_object(self.flow_specs["src_hosts"][i])
            dst_h_obj = self.nc.ng.get_node_object(self.flow_specs["dst_hosts"][i])

            src_ports.append((src_h_obj.sw.node_id, src_h_obj.switch_port.port_number))
            dst_ports.append((dst_h_obj.sw.node_id, dst_h_obj.switch_port.port_number))

        flows = self.get_rpc_flows(src_ports, dst_ports)

        reps = []
        for rep in self.reps:
            link_failure_sequence = []
            for f in rep['failures']:
                link_failure_sequence.append(self.rpc_links["s" + str(f[1]+1)]["s" + str(f[2]+1)])

            reps.append(flow_validator_pb2.NumActiveFlowsRep(link_failure_sequence=link_failure_sequence,
                                                             num_active_flows=[]))

        nafp = flow_validator_pb2.NumActiveFlowsParams(flows=flows, reps=reps)

        nafi = self.stub.GetNumActiveFlowsAtFailureTimes(nafp)

        for i in xrange(len(nafi.reps)):
            self.input["reps"][i]["num_active_flows"] = list(nafi.reps[i].num_active_flows)

        print self.input["reps"]

        with open('output.json', "w") as json_file:
            json.dump(self.input, json_file)

    def trigger(self):
        self.channel = grpc.insecure_channel('localhost:50051')
        self.stub = flow_validator_pb2_grpc.FlowValidatorStub(self.channel)

        self.flow_validator_initialize()

        # self.flow_validator_get_time_to_failure()

        self.flow_validator_get_num_active_flows_at_failure_times()


def main():

    flow_specs = {"src_hosts": [], "dst_hosts": []}

    with open('dump.json') as json_file:
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


if __name__ == "__main__":
    main()

