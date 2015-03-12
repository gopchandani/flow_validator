__author__ = 'Rakesh Kumar'


from timer import Timer
from analysis.flow_validator import FlowValidator


def main():
    bp = FlowValidator()
    bp.add_hosts()

    with Timer(verbose=True) as t:
         bp.initialize_admitted_match()
    print "=> elasped initialize_admitted_match: %s ms" % t.msecs

    bp.validate_all_host_pair_basic_reachability()

if __name__ == "__main__":
    main()
