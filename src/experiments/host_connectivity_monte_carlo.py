__author__ = 'Rakesh Kumar'

import sys

sys.path.append("./")

import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as ss

from collections import defaultdict
from timer import Timer
from analysis.flow_validator import FlowValidator
from experiment import Experiment


class MonteCarlo(Experiment):
    def __init__(self,
                 num_iterations,
                 load_config,
                 save_config,
                 controller,
                 fanout,
                 core,
                 total_number_of_ports_to_synthesize,
                 numbers_of_monte_carlo_runs):

        super(MonteCarlo, self).__init__("monte_carlo",
                                         num_iterations,
                                         load_config,
                                         save_config,
                                         controller,
                                         1)

        self.total_number_of_ports_to_synthesize = total_number_of_ports_to_synthesize

        self.fanout = fanout
        self.core = core

        self.numbers_of_monte_carlo_runs = numbers_of_monte_carlo_runs

        self.data = {
            "execution_time": defaultdict(defaultdict),
            "number_of_edges_to_break_estimate": defaultdict(defaultdict),
            "number_of_edges_to_break_estimate_data": defaultdict(defaultdict),
        }

    def perform_monte_carlo(self, num_runs):
        run_values = []
        run_edges = []

        for i in xrange(num_runs):

            print "Performing Run:", i + 1

            broken_edges = self.fv.break_random_edges_until_any_pair_disconnected(verbose=False)
            #broken_edges = self.fv.break_specified_edges_in_order([('s2', 's7'), ('s3', 's7')], verbose=True)
            #broken_edges = self.fv.break_specified_edges_in_order([('s1', 's4')], verbose=True)

            num_edges = len(broken_edges)

            if num_edges < 2:
                pass

            run_edges.append(broken_edges)
            run_values.append(num_edges)

        runs_mean = np.mean(run_values)
        runs_sem = ss.sem(run_values)

        print run_values
        print run_edges

        return run_values, runs_mean, runs_sem

    def trigger(self):

        print "Starting experiment..."

        for number_of_ports_to_synthesize in range(1, self.total_number_of_ports_to_synthesize + 1):
            ports_to_synthesize = range(5000, 5000 + number_of_ports_to_synthesize)
            print "ports_to_synthesize:", ports_to_synthesize

            self.topo_description = ("ring", 4, 1, None, None)
            #self.topo_description = ("clostopo", None, 1, self.fanout, self.core)

            ng = self.setup_network_graph(self.topo_description,
                                          mininet_setup_gap=1,
                                          dst_ports_to_synthesize=None,
                                          synthesis_setup_gap=60,
                                          synthesis_scheme="IntentSynthesis")

            self.fv = FlowValidator(ng)
            self.fv.init_port_graph()
            self.fv.add_hosts()
            self.fv.initialize_admitted_traffic()


            # import objgraph
            # objgraph.show_most_common_types()


            print "Initialization done."

            for number_of_monte_carlo_runs in self.numbers_of_monte_carlo_runs:
                print "number_of_monte_carlo_runs:", number_of_monte_carlo_runs

                self.data["execution_time"][number_of_ports_to_synthesize][number_of_monte_carlo_runs] = []
                self.data["number_of_edges_to_break_estimate"][number_of_ports_to_synthesize][number_of_monte_carlo_runs] = []
                self.data["number_of_edges_to_break_estimate_data"][number_of_ports_to_synthesize][number_of_monte_carlo_runs] = []

                for i in range(self.num_iterations):
                    print "iteration:", i + 1

                    with Timer(verbose=True) as t:
                        est = self.perform_monte_carlo(number_of_monte_carlo_runs)

                    self.data["execution_time"][number_of_ports_to_synthesize][number_of_monte_carlo_runs].append(t.msecs)
                    self.data["number_of_edges_to_break_estimate"][number_of_ports_to_synthesize][number_of_monte_carlo_runs].append(est[1])
                    self.data["number_of_edges_to_break_estimate_data"][number_of_ports_to_synthesize][number_of_monte_carlo_runs].append(est)

            self.fv.de_init_port_graph()

    def plot_monte_carlo(self):
        fig = plt.figure(0)
        self.plot_line_error_bars("execution_time",
                                  "Number of Monte Carlo Runs",
                                  "Execution Time (ms)",
                                  y_scale='linear')

        fig = plt.figure(0)
        self.plot_line_error_bars("number_of_edges_to_break_estimate",
                                  "Number of Monte Carlo Runs",
                                  "Estimated number of links to break",
                                  y_scale='linear')

def main():
    num_iterations = 1#20
    load_config = False
    save_config = True
    controller = "ryu"

    fanout = 2
    core = 1
    total_number_of_ports_to_synthesize = 1
    numbers_of_monte_carlo_runs = [10]#[10, 20, 30]

    exp = MonteCarlo(num_iterations,
                     load_config,
                     save_config,
                     controller,
                     fanout,
                     core,
                     total_number_of_ports_to_synthesize,
                     numbers_of_monte_carlo_runs)

    exp.trigger()
    #exp.dump_data()

    #exp.load_data("data/monte_carlo_3_iterations_20151205_134951.json")
    #exp.plot_monte_carlo()


if __name__ == "__main__":
    main()
