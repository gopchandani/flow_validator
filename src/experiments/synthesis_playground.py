import sys

from experiment import Experiment
from model.traffic import Traffic
from analysis.flow_validator import FlowValidator

__author__ = 'Rakesh Kumar'

sys.path.append("./")

class SynthesisPlayground(Experiment):

    def __init__(self,
                 num_iterations,
                 num_hosts_per_switch,
                 load_config,
                 save_config,
                 controller):

        super(SynthesisPlayground, self).__init__("number_of_hosts",
                                                   num_iterations,
                                                   load_config,
                                                   save_config,
                                                   controller,
                                                   len(num_hosts_per_switch))

        self.num_hosts_per_switch = num_hosts_per_switch
        self.num_iterations = num_iterations

    def trigger(self):

        print "Starting experiment..."
        for num_hosts_per_switch in self.num_hosts_per_switch:

            print "num_hosts_per_switch:", num_hosts_per_switch

            self.topo_description = ("ring", 4, num_hosts_per_switch, None, None)
            #self.topo_description = ("clostopo", 7, num_hosts_per_switch, 2, 1)

            ng = self.setup_network_graph(self.topo_description,
                                          mininet_setup_gap=5,
                                          synthesis_scheme="Synthesis_Failover_Aborescene",
                                          synthesis_setup_gap=5)

            fv = FlowValidator(ng)
            fv.init_network_port_graph()
            fv.add_hosts()
            fv.initialize_admitted_traffic()

            src_zone = [fv.network_graph.get_node_object(h_id).get_switch_port() for h_id in fv.network_graph.host_ids]
            dst_zone = [fv.network_graph.get_node_object(h_id).get_switch_port() for h_id in fv.network_graph.host_ids]

            # src_zone = [fv.network_graph.get_node_object("h11").switch_port]
            # dst_zone = [fv.network_graph.get_node_object("h21").switch_port]

            specific_traffic = Traffic(init_wildcard=True)
            specific_traffic.set_field("ethernet_type", 0x0800)

            connected = fv.validate_zone_pair_connectivity(src_zone, dst_zone, specific_traffic, 0)
            print connected

            connected = fv.validate_zone_pair_connectivity(src_zone, dst_zone, specific_traffic, 1)
            print connected

        print "Done..."

def main():

    num_iterations = 1#10
    num_hosts_per_switch = [1]#, 2, 3, 4]
    load_config = False
    save_config = True


    controller = "ryu"

    exp = SynthesisPlayground(num_iterations,
                               num_hosts_per_switch,
                               load_config,
                               save_config,
                               controller)

    exp.trigger()

if __name__ == "__main__":
    main()