__author__ = 'Rakesh Kumar'

import sys
sys.path.append("./")

from experiment import Experiment

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

            #self.topo_description = ("ring", 4, 1, None, None)
            self.topo_description = ("clostopo", None, 1, 3, 1)

            ng = self.setup_network_graph(self.topo_description,
                                          #synthesis_scheme="Synthesis_Simple_Aborescene",
                                          synthesis_scheme="Synthesis_Failover_Aborescene",
                                          synthesis_setup_gap=5)


        print "Done..."

def main():

    num_iterations = 1#10
    total_number_of_hosts = [4]
    load_config = False
    save_config = True
    controller = "ryu"

    exp = AborescenePlayground(num_iterations,
                               total_number_of_hosts,
                               load_config,
                               save_config,
                               controller)

    exp.trigger()

if __name__ == "__main__":
    main()