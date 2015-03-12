__author__ = 'Rakesh Kumar'

from timer import Timer
from analysis.flow_validator import FlowValidator



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

def main():
    init_time()

if __name__ == "__main__":
    main()
