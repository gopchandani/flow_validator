__author__ = 'Rakesh Kumar'

from timer import Timer
from analysis.flow_validator import FlowValidator
from topology.controller_man import ControllerMan

def init_time():

    num_iterations = 10
    init_times = []

    for i in range(num_iterations):

        bp = FlowValidator()
        bp.add_hosts()

        with Timer(verbose=True) as t:
            bp.initialize_admitted_match()

        init_times.append(t.msecs)

    print init_times


def put_together_network():
    cm = ControllerMan(5)

	for i in range (num_cons):
		print "Container with port number",
		print ports[i],
		print "has container id",
		print data[i]

def main():
    put_together_network()
    #init_time()

if __name__ == "__main__":
    main()
