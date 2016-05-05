__author__ = 'Rakesh Kumar'

import sys
sys.path.append("./")

from experiment import Experiment
from model.traffic import Traffic
from analysis.flow_validator import FlowValidator

class AborescenePlayground(Experiment):

    def __init__(self,
                 num_iterations,
                 total_number_of_hosts,
                 load_config,
                 save_config,
                 controller):

        super(AborescenePlayground, self).__init__("number_of_hosts",
                                                   num_iterations,
                                                   load_config,
                                                   save_config,
                                                   controller,
                                                   len(total_number_of_hosts))

        self.total_number_of_hosts = total_number_of_hosts

    def trigger(self):

        print "Starting experiment..."
        for total_number_of_hosts in self.total_number_of_hosts:

            self.topo_description = ("ring", 4, 1, None, None)
            #self.topo_description = ("clostopo", None, 1, 2, 1)
            #self.topo_description = ("linear", 2, 1)

            ng = self.setup_network_graph(self.topo_description,
                                          synthesis_scheme="Synthesis_Failover_Aborescene",
                                          synthesis_setup_gap=5)

            fv = FlowValidator(ng)
            fv.init_network_port_graph()
            fv.add_hosts()
            fv.initialize_admitted_traffic()

#            src_zone = [fv.network_graph.get_node_object(h_id).switch_port for h_id in fv.network_graph.host_ids]
#            dst_zone = [fv.network_graph.get_node_object(h_id).switch_port for h_id in fv.network_graph.host_ids]

            # specific_traffic = Traffic(init_wildcard=True)
            # specific_traffic.set_field("ethernet_type", 0x0800)
            # connected = fv.validate_zone_pair_connectivity(src_zone, dst_zone, specific_traffic, 0)
            # print connected
            #
            # connected = fv.validate_zone_pair_connectivity(src_zone, dst_zone, specific_traffic, 1)
            # print connected


            src_zone = [fv.network_graph.get_node_object("h11").switch_port]
            dst_zone = [fv.network_graph.get_node_object("h21").switch_port]

            specific_traffic = Traffic(init_wildcard=True)
            specific_traffic.set_field("ethernet_type", 0x0800)

            connected = fv.validate_zone_pair_connectivity(src_zone, dst_zone, specific_traffic, 0)
            print connected

            # connected = fv.validate_zone_pair_connectivity(dst_zone, src_zone, specific_traffic, 0)
            # print connected

            connected = fv.validate_zone_pair_connectivity(src_zone, dst_zone, specific_traffic, 1)
            print connected

            # connected = fv.validate_zone_pair_connectivity(dst_zone, src_zone, specific_traffic, 1)
            # print connected

        print "Done..."

def main():

    num_iterations = 1#10
    total_number_of_hosts = [4]
    load_config = True
    save_config = False
    controller = "ryu"

    exp = AborescenePlayground(num_iterations,
                               total_number_of_hosts,
                               load_config,
                               save_config,
                               controller)

    exp.trigger()

if __name__ == "__main__":
    main()