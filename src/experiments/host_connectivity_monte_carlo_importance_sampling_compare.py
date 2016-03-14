__author__ = 'Rakesh Kumar'

import sys

sys.path.append("./")

import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as ss

from collections import defaultdict
from timer import Timer
from analysis.monte_carlo_analysis import MonteCarloAnalysis
from experiment import Experiment

class HostConnectivityMonteCarloImportanceSamplingCompare(Experiment):
    def __init__(self,
                 num_iterations,
                 load_config,
                 save_config,
                 controller,
                 fanout,
                 core,
                 total_number_of_ports_to_synthesize,
                 numbers_of_monte_carlo_runs):

        super(HostConnectivityMonteCarloImportanceSamplingCompare, self).__init__("monte_carlo",
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
            "number_of_links_to_break_estimate": defaultdict(defaultdict),
            "number_of_links_to_break_estimate_data": defaultdict(defaultdict),
        }

    def perform_monte_carlo(self, num_runs):
        run_links = []
        run_values = []

        for i in xrange(num_runs):

            print "Performing Run:", i + 1

            run_value, run_broken_links = self.mca.break_random_links_until_any_pair_disconnected(verbose=False)
            run_links.append(run_broken_links)
            run_values.append(run_value)

        run_mean = np.mean(run_values)
        run_sem = ss.sem(run_values)

        return run_links, run_values, run_mean, run_sem

    def perform_monte_carlo_importance_sampling(self, num_unskewed_runs, num_runs):

        unskewed_run_links, unskewed_run_values, unskewed_run_mean, unskewed_run_sem = self.perform_monte_carlo(num_unskewed_runs)

        skewed_run_links = []
        skewed_run_values = []

        for i in xrange(num_runs - num_unskewed_runs):

            print "Performing Run:", i + 1 + num_unskewed_runs
            run_value, run_broken_links =  self.mca.break_random_links_until_any_pair_disconnected_importance(unskewed_run_mean, verbose=False)
            skewed_run_links.append(run_broken_links)
            skewed_run_values.append(run_value)

        run_links = unskewed_run_links + skewed_run_links
        run_values = unskewed_run_values + skewed_run_values

        run_mean = np.mean(run_values)
        run_sem = ss.sem(run_values)

        return run_links, run_values, run_mean, run_sem

    def trigger(self):

        print "Starting experiment..."

        for number_of_ports_to_synthesize in xrange(1, self.total_number_of_ports_to_synthesize + 1):
            ports_to_synthesize = xrange(5000, 5000 + number_of_ports_to_synthesize)
            print "ports_to_synthesize:", ports_to_synthesize

            #self.topo_description = ("ring", 4, 1, None, None)
            self.topo_description = ("clostopo", None, 1, self.fanout, self.core)

            ng = self.setup_network_graph(self.topo_description,
                                          mininet_setup_gap=1,
                                          dst_ports_to_synthesize=None,
                                          synthesis_setup_gap=60,
                                          synthesis_scheme="IntentSynthesis")

            self.mca = MonteCarloAnalysis(ng)
            self.mca.init_network_port_graph()
            self.mca.add_hosts()
            self.mca.initialize_admitted_traffic()

            print "Initialization done."

            for total_runs in self.numbers_of_monte_carlo_runs:
                print "total_runs:", total_runs

                self.data["execution_time"][number_of_ports_to_synthesize][total_runs] = []
                self.data["number_of_links_to_break_estimate"][number_of_ports_to_synthesize][total_runs] = []
                self.data["number_of_links_to_break_estimate_data"][number_of_ports_to_synthesize][total_runs] = []

                for i in xrange(self.num_iterations):
                    print "iteration:", i + 1

                    with Timer(verbose=True) as t:
                        est = self.perform_monte_carlo(total_runs)

                    print "est:", est[2], est[3]

                    # self.data["execution_time"][number_of_ports_to_synthesize][total_runs].append(t.msecs)
                    # self.data["number_of_links_to_break_estimate"][number_of_ports_to_synthesize][total_runs].append(est[1])
                    # self.data["number_of_links_to_break_estimate_data"][number_of_ports_to_synthesize][total_runs].append(est)

                    with Timer(verbose=True) as t:
                        est = self.perform_monte_carlo_importance_sampling(5, total_runs)

                    print "est:", est[2], est[3]


            self.mca.de_init_network_port_graph()

    def plot_monte_carlo(self):
        fig = plt.figure(0)
        self.plot_line_error_bars("execution_time",
                                  "Number of Monte Carlo Runs",
                                  "Execution Time (ms)",
                                  y_scale='linear')

        fig = plt.figure(0)
        self.plot_line_error_bars("number_of_links_to_break_estimate",
                                  "Number of Monte Carlo Runs",
                                  "Estimated number of links to break",
                                  y_scale='linear')

def main():
    num_iterations = 1#20
    load_config = True
    save_config = False
    controller = "ryu"

    fanout = 2
    core = 1

    total_number_of_ports_to_synthesize = 1
    numbers_of_monte_carlo_runs = [10]#[10, 20, 30]

    exp = HostConnectivityMonteCarloImportanceSamplingCompare(num_iterations,
                                                              load_config,
                                                              save_config,
                                                              controller,
                                                              fanout,
                                                              core,
                                                              total_number_of_ports_to_synthesize,
                                                              numbers_of_monte_carlo_runs)

    exp.trigger()
    exp.dump_data()

    #exp.load_data("data/monte_carlo_3_iterations_20151205_134951.json")
    #exp.plot_monte_carlo()

if __name__ == "__main__":
    main()
