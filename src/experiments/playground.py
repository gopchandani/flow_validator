import sys

from experiment import Experiment
from experiments.network_configuration import NetworkConfiguration
from model.traffic import Traffic
from analysis.flow_validator import FlowValidator
from analysis.policy_statement import PolicyStatement, PolicyConstraint
from analysis.policy_statement import CONNECTIVITY_CONSTRAINT

__author__ = 'Rakesh Kumar'

sys.path.append("./")


class Playground(Experiment):

    def __init__(self, nc):

        super(Playground, self).__init__("playground", 1)

        self.nc = nc

    def trigger(self):

        ng = self.nc.setup_network_graph(mininet_setup_gap=1, synthesis_setup_gap=1)

        fv = FlowValidator(ng)
        fv.init_network_port_graph()

        src_zone = [fv.network_graph.get_node_object(h_id).switch_port for h_id in ['h31']]#fv.network_graph.host_ids]
        dst_zone = [fv.network_graph.get_node_object(h_id).switch_port for h_id in ['h11']]#fv.network_graph.host_ids]

        specific_traffic = Traffic(init_wildcard=True)
        specific_traffic.set_field("ethernet_type", 0x0800)

        constraints = [PolicyConstraint(CONNECTIVITY_CONSTRAINT, None)]

        s = PolicyStatement(self.nc.ng,
                            src_zone,
                            dst_zone,
                            specific_traffic,
                            constraints,
                            lmbdas=[tuple(ng.get_switch_link_data(sw=ng.get_node_object("s4")))])

        violations = fv.validate_policy([s])

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
                               "per_switch_links": 2},
                              conf_root="configurations/",
                              #synthesis_name="DijkstraSynthesis",
                              synthesis_name="AboresceneSynthesis",
                              synthesis_params={"apply_group_intents_immediately": True})

    exp = Playground(nc)
    exp.trigger()


if __name__ == "__main__":
    main()
