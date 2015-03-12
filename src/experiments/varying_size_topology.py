__author__ = 'Rakesh Kumar'

from timer import Timer
from analysis.flow_validator import FlowValidator
from topology.controller_man import ControllerMan

class VaryingSizeTopology():

    def __init__(self):

        # Get the docker ready
        self.cm = ControllerMan(3)

    def init_time(self):

        num_iterations = 10
        init_times = []

        for i in range(num_iterations):

            bp = FlowValidator()
            bp.add_hosts()

            with Timer(verbose=True) as t:
                bp.initialize_admitted_match()

            init_times.append(t.msecs)

        print init_times

    def setup_network(self):

        # First get a docker for controller
        controller_port = self.cm.get_next()

def main():

    exp = VaryingSizeTopology()
    exp.setup_network()

    #init_time()

if __name__ == "__main__":
    main()
