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

class UniformImportanceSamplingCompare(Experiment):
    def __init__(self,
                 num_iterations,
                 load_config,
                 save_config,
                 controller,
                 topo_descriptions,
                 expected_values,
                 num_seed_runs,
                 error_bounds):

        super(UniformImportanceSamplingCompare, self).__init__("uniform_importance_sampling_compare",
                                                               num_iterations,
                                                               load_config,
                                                               save_config,
                                                               controller,
                                                               1)

        self.topo_descriptions = topo_descriptions
        self.expected_values = expected_values
        self.num_seed_runs = num_seed_runs
        self.error_bounds = error_bounds

        self.data = {
            "execution_time": defaultdict(defaultdict),
            "num_required_runs": defaultdict(defaultdict),
        }

    def perform_monte_carlo(self, num_runs):
        run_links = []
        run_values = []

        for i in xrange(num_runs):

            run_value, run_broken_links = self.mca.break_random_links_until_any_pair_disconnected(verbose=False)
            run_links.append(run_broken_links)
            run_values.append(run_value)

        run_mean = np.mean(run_values)
        run_sem = ss.sem(run_values)

        return run_mean, run_sem

    def compute_num_required_runs(self, expected_value, error_bound, sampling, num_seed_runs=None):
        run_links = []
        run_values = []

        required_lower_bound = expected_value - expected_value * error_bound
        required_upper_bound = expected_value + expected_value * error_bound

        num_required_runs = 0
        reached_bound = False

        seed_mean = None
        seed_sem = None

        if sampling == "importance":
            seed_mean, seed_sem = self.perform_monte_carlo(num_seed_runs)

        while not reached_bound:

            run_value = None
            run_broken_links = None

            if sampling == "uniform":
                run_value, run_broken_links = self.mca.break_random_links_until_any_pair_disconnected(verbose=False)
            elif sampling == "importance":
                run_value, run_broken_links = self.mca.break_random_links_until_any_pair_disconnected_importance(seed_mean,
                                                                                                                 verbose=False)
            run_links.append(run_broken_links)
            run_values.append(run_value)

            # Do at least two runs...
            if num_required_runs > 0:

                run_mean = np.mean(run_values)
                run_sem = ss.sem(run_values)

                run_lower_bound = run_mean - run_sem
                run_upper_bound = run_mean + run_sem

                print "run_mean:", run_mean

                if required_lower_bound <= run_lower_bound and run_upper_bound <= required_upper_bound:
                    reached_bound = True

            num_required_runs += 1
            print sampling, "runs so far:", num_required_runs

        if sampling == "importance":
            num_required_runs += num_seed_runs

        return num_required_runs

    def trigger(self):

        print "Starting experiment..."

        for i in range(len(self.topo_descriptions)):

            topo_description = self.topo_descriptions[i]

            ng = self.setup_network_graph(topo_description,
                                          mininet_setup_gap=1,
                                          dst_ports_to_synthesize=None,
                                          synthesis_setup_gap=60,
                                          synthesis_scheme="IntentSynthesis")

            self.mca = MonteCarloAnalysis(ng)
            self.mca.init_network_port_graph()
            self.mca.add_hosts()
            self.mca.initialize_admitted_traffic()

            #self.mca.test_classification_breaking_specified_link_sequence([('s1', 's2'), ('s2', 's4')])
            #
            # self.mca.compute_e_nf_exhaustive()
            # return

            # for p in self.mca.generate_link_permutation():
            #     print p

            #return

            print "Initialization done."

            # scenario_keys = (topo_description[0] + "_" + str(topo_description[1]) + "_" + "uniform",
            #                  topo_description[0] + "_" + str(topo_description[1]) + "_"+ "importance")

            scenario_keys = (topo_description[0] + " with " + str(topo_description[1]) + " switches using uniform sampling",
                             topo_description[0] + " with " + str(topo_description[1]) + " switches using importance sampling")

            for error_bound in self.error_bounds:

                self.data["execution_time"][scenario_keys[0]][error_bound] = []
                self.data["num_required_runs"][scenario_keys[0]][error_bound] = []

                self.data["execution_time"][scenario_keys[1]][error_bound] = []
                self.data["num_required_runs"][scenario_keys[1]][error_bound] = []

                for j in xrange(self.num_iterations):
                    print "iteration:", j + 1
                    print "num_seed_runs:", self.num_seed_runs

                    with Timer(verbose=True) as t:
                        num_required_runs = self.compute_num_required_runs(self.expected_values[i],
                                                                           float(error_bound)/100,
                                                                           "uniform")

                    self.data["execution_time"][scenario_keys[0]][error_bound].append(t.msecs)
                    self.data["num_required_runs"][scenario_keys[0]][error_bound].append(num_required_runs)

                    with Timer(verbose=True) as t:
                        num_required_runs = self.compute_num_required_runs(self.expected_values[i],
                                                                           float(error_bound)/100,
                                                                           "importance",
                                                                           self.num_seed_runs)

                    self.data["execution_time"][scenario_keys[1]][error_bound].append(t.msecs)
                    self.data["num_required_runs"][scenario_keys[1]][error_bound].append(num_required_runs)

            self.mca.de_init_network_port_graph()

    def plot_monte_carlo(self):
        # fig = plt.figure(0)
        # self.plot_line_error_bars("execution_time",
        #                           "Number of Monte Carlo Runs",
        #                           "Execution Time (ms)",
        #                           y_scale='linear')

        fig = plt.figure(0)
        self.plot_line_error_bars("num_required_runs",
                                  "Relative Error",
                                  "Average Number of Runs",
                                  y_scale='log',
                                  line_label="",
                                  line_label_suffixes=[],
                                  xmax_factor=1.05,
                                  xmin_factor=0.5,
                                  y_max_factor=1.05,
                                  legend_loc='upper right',
                                  xticks=[2, 5, 10], xtick_labels=["0.02", "0.05", "0.1"])

def main():
    num_iterations = 10
    load_config = True
    save_config = False
    controller = "ryu"

    #topo_descriptions = [("ring", 4, 1, None, None)]
    #topo_descriptions = [("ring", 6, 1, None, None)]
    topo_descriptions = [("ring", 8, 1, None, None)]
    #topo_descriptions = [("ring", 10, 1, None, None)]

    #topo_descriptions = [("clostopo", None, 1, 2, 1)]
    #topo_descriptions = [("clostopo", None, 1, 2, 2)]

    #expected_values = [2.33]
    #expected_values = [2.5]
    expected_values = [2.6]
    #expected_values = [2.77142857143]

    #expected_values = [5.00]
    #expected_values = [19.50]

    # topo_descriptions = [("ring", 4, 1, None, None),
    #                      ("ring", 6, 1, None, None),
    #                      ("ring", 8, 1, None, None),
    #                      ("ring", 10, 1, None, None)]
    #
    # expected_values = [2.33, 2.5, 2.16, 2.77142857143]

    num_seed_runs = 10
    error_bounds = ["2", "5", "10"]#, "5","10"]

    exp = UniformImportanceSamplingCompare(num_iterations,
                                           load_config,
                                           save_config,
                                           controller,
                                           topo_descriptions,
                                           expected_values,
                                           num_seed_runs,
                                           error_bounds)

    exp.trigger()
    exp.dump_data()

    #exp.load_data("data/uniform_importance_sampling_compare_5_iterations_20160315_215918.json")
    #exp.load_data("data/uniform_importance_sampling_compare_10_iterations_20160316_202014.json")
    #exp.load_data("data/uniform_importance_sampling_compare_10_iterations_20160319_075926.json")

    #exp.load_data("data/uniform_importance_sampling_compare_2_iterations_20160321_204907.json")

    #exp.load_data("data/uniform_importance_sampling_compare_3_iterations_20160322_051218.json")

    #Candidate
    #exp.load_data("data/uniform_importance_sampling_compare_3_iterations_20160323_073307.json")

    exp.plot_monte_carlo()

if __name__ == "__main__":
    main()
