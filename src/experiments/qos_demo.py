__author__ = 'Rakesh Kumar'

import sys
sys.path.append("./")

from experiment import Experiment

class QosDemo(Experiment):

    def __init__(self,
                 num_iterations,
                 total_number_of_hosts,
                 load_config,
                 save_config,
                 controller,
                 experiment_switches):

        super(QosDemo, self).__init__("number_of_hosts",
                                            num_iterations,
                                            load_config,
                                            save_config,
                                            controller,
                                            experiment_switches,
                                            len(total_number_of_hosts))

        self.total_number_of_hosts = total_number_of_hosts

    def trigger(self):

        print "Starting experiment..."
        for total_number_of_hosts in self.total_number_of_hosts:

            self.topo_description = ("linear", 2, total_number_of_hosts/2)
            ng = self.setup_network_graph(self.topo_description, qos=True)

        print "Done..."

def main():

    num_iterations = 1#10
    total_number_of_hosts = [4]#, 6, 8, 10]# 14, 16])#, 18, 20]
    load_config = False
    save_config = True
    controller = "ryu"
    experiment_switches = ["s1", "s2"]

    exp = QosDemo(num_iterations,
                        total_number_of_hosts,
                        load_config,
                        save_config,
                        controller,
                        experiment_switches)

    exp.trigger()

if __name__ == "__main__":
    main()