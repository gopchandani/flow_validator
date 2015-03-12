__author__ = 'Rakesh Kumar'

import sys
sys.path.append("./")

from timer import Timer
from analysis.flow_validator import FlowValidator
from topology.controller_man import ControllerMan
from topology.mininet_man import MininetMan

class VaryingSizeTopology():

    def __init__(self, sample_size, topology_sizes):

        self.num_iterations = sample_size
        self.topology_sizes = topology_sizes
        self.init_times = {}


        # Get the dockers ready
        #self.cm = ControllerMan(len(topology_sizes))
        self.cm = ControllerMan(3)


    def setup_network(self, topology_size):

        # First get a docker for controller
        controller_port = self.cm.get_next()
        print "Controller Port", controller_port

        self.mm = MininetMan(controller_port, "ring", topology_size, 1)
        self.mm.setup_mininet()

    def trigger(self):

        for topology_size in self.topology_sizes:

            self.setup_network(topology_size)
            self.init_times[topology_size] = []

            for i in range(self.num_iterations):

                bp = FlowValidator()
                bp.add_hosts()

                with Timer(verbose=True) as t:
                    bp.initialize_admitted_match()

                self.init_times[topology_size].append(t.msecs)

            print topology_size, self.init_times[topology_size]

        print self.init_times

def main():

    exp = VaryingSizeTopology(10, [4])
    exp.trigger()

if __name__ == "__main__":
    main()
