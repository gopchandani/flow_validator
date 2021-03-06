import sys
import itertools
from experiment import Experiment
from experiments.network_configuration import NetworkConfiguration
from model.traffic import Traffic
from analysis.flow_validator import FlowValidator
from analysis.policy_statement import PolicyStatement, PolicyConstraint
from analysis.policy_statement import CONNECTIVITY_CONSTRAINT, LINK_AVOIDANCE_CONSTRAINT

__author__ = 'Rakesh Kumar'

sys.path.append("./")


class Playground(Experiment):

    def __init__(self, nc):

        super(Playground, self).__init__("playground", 1)

        self.nc = nc

    def trigger(self):

        ng = self.nc.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

        # fv = FlowValidator(ng)
        # specific_traffic = Traffic(init_wildcard=True)
        # specific_traffic.set_field("ethernet_type", 0x0800)

        fv = FlowValidator(ng, use_sdnsim=True, nc=self.nc)
        specific_traffic = dict()
        specific_traffic["eth_type"] = 0x0800

        src_zone = [fv.network_graph.get_node_object(h_id).switch_port for h_id in fv.network_graph.host_ids]
        dst_zone = [fv.network_graph.get_node_object(h_id).switch_port for h_id in fv.network_graph.host_ids]
        lmbdas = list(itertools.permutations(ng.L, 2))

        constraints = [PolicyConstraint(CONNECTIVITY_CONSTRAINT, None)]

        # l = tuple(ng.get_switch_link_data(sw=ng.get_node_object("s3")))
        # l = l[:-1]
        # print l
        #
        # src_zone = [fv.network_graph.get_node_object(h_id).switch_port for h_id in ['h41']]
        # dst_zone = [fv.network_graph.get_node_object(h_id).switch_port for h_id in ['h11']]
        lmbdas = [(ng.get_link_data('s3', 's1'),
                   ng.get_link_data('s3', 's4'),
                   ng.get_link_data('s3', 's2')
                   )]

        s = PolicyStatement(self.nc.ng,
                            src_zone,
                            dst_zone,
                            specific_traffic,
                            constraints,
                            lmbdas=lmbdas)

        violations = fv.validate_policy([s])

        for v in violations:
            print v.src_port, v.dst_port, v.constraint

        print "Total violations:", len(violations)


def main():
    nc = NetworkConfiguration("ryu",
                              "127.0.0.1",
                              6633,
                              "http://localhost:8080/",
                              "admin",
                              "admin",
                              "cliquetopo",
                              {"num_switches": 4,
                               "num_hosts_per_switch": 1,
                               "per_switch_links": 3},
                              conf_root="configurations/",
                              # synthesis_name="DijkstraSynthesis",
                              # synthesis_params={"apply_group_intents_immediately": True})
                              synthesis_name="AboresceneSynthesis",
                              synthesis_params={"apply_group_intents_immediately": True,
                                                "k": 2})

    exp = Playground(nc)
    exp.trigger()


if __name__ == "__main__":
    main()
