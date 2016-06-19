__author__ = 'Rakesh Kumar'

import sys
import json
sys.path.append("./")

import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as ss

from collections import defaultdict
from timer import Timer
from analysis.monte_carlo_analysis import MonteCarloAnalysis
from experiment import Experiment
from network_configuration import NetworkConfiguration


class MonteCarloSamplingCompare(Experiment):
    def __init__(self,
                 network_configurations,
                 num_iterations,
                 num_seed_runs,
                 relative_errors,
                 expected_values):

        super(MonteCarloSamplingCompare, self).__init__("monte_carlo_sampling_compare",
                                                        num_iterations)

        self.network_configurations = network_configurations
        self.num_seed_runs = num_seed_runs
        self.relative_errors = relative_errors
        self.expected_values = expected_values

        self.data = {
            "execution_time": defaultdict(defaultdict),
            "num_required_runs": defaultdict(defaultdict),
        }

    def perform_seed_runs(self, num_runs):
        run_links = []
        run_values = []

        for i in xrange(num_runs):

            run_value, run_broken_links = self.mca.break_random_links_until_any_pair_disconnected_uniform(verbose=False)
            run_links.append(run_broken_links)
            run_values.append(run_value)

        run_mean = np.mean(run_values)
        run_sd = np.std(run_values)

        return run_mean, run_sd

    def compute_num_required_runs(self, expected_value, relative_error, sampling_type, num_min_runs, num_seed_runs=None):
        run_links = []
        run_values = []

        required_lower_bound = expected_value - expected_value * relative_error
        required_upper_bound = expected_value + expected_value * relative_error

        num_required_runs = 0
        reached_bound = False

        if sampling_type == "importance":
            seed_mean, seed_sd = self.perform_seed_runs(num_seed_runs)
            print "seed_mean:", seed_mean

        while not reached_bound:

            run_value = None
            run_broken_links = None

            if sampling_type == "uniform":
                run_value, run_broken_links = self.mca.break_random_links_until_any_pair_disconnected_uniform(verbose=False)
            elif sampling_type == "importance":
                run_value, run_broken_links = self.mca.break_random_links_until_any_pair_disconnected_importance(seed_mean,
                                                                                                                 verbose=False)
            run_links.append(run_broken_links)
            run_values.append(run_value)

            # Do at least num_min_runs
            if num_required_runs > 0 and num_required_runs % num_min_runs == 0:

                run_mean = np.mean(run_values)
                run_sd = np.std(run_values)

                print sampling_type, "runs so far:", num_required_runs

                print "run_mean:", run_mean
                t99 = 2.56

                plus_minus = t99 * run_sd / np.sqrt(num_required_runs - 1)

                print "plus_minus:", plus_minus

                interval_percentage = 100 * (2*plus_minus/run_mean)

                print "interval_percentage:", interval_percentage

                if interval_percentage <= relative_error:
                    reached_bound = True

            num_required_runs += 1

        if sampling_type == "importance":
            num_required_runs += num_seed_runs

        run_lower_bound = run_mean - plus_minus
        run_upper_bound = run_mean + plus_minus

        if required_lower_bound <= run_lower_bound and run_upper_bound <= required_upper_bound:
            print "Reached CI meets expected value bound"
        else:
            print "Reached CI does not meet expected value bound"

        return num_required_runs

    def trigger(self):

        print "Starting experiment..."

        for i in range(len(self.network_configurations)):

            nc = self.network_configurations[i]

            ng = self.setup_network_graph(nc,
                                          mininet_setup_gap=1,
                                          synthesis_setup_gap=60)

            self.mca = MonteCarloAnalysis(ng, False)
            self.mca.init_network_port_graph()
            self.mca.add_hosts()
            self.mca.initialize_admitted_traffic()

            # self.mca.test_classification_breaking_specified_link_sequence([('s2', 's3'), ('s4', 's3')])
            # self.mca.test_classification_breaking_specified_link_sequence([('s2', 's3'), ('s4', 's1')])

            # self.mca.compute_e_nf_exhaustive()
            # return

            print "Initialization done."

            # scenario_keys = (topo_description[0] + "_" + str(topo_description[1]) + "_" + "uniform",
            #                  topo_description[0] + "_" + str(topo_description[1]) + "_"+ "importance")

            scenario_keys = (nc.topo_name + " with " + str(nc.topo_params["num_switches"]) + " switches using uniform sampling",
                             nc.topo_name + " with " + str(nc.topo_params["num_switches"]) + " switches using importance sampling")

            for relative_error in self.relative_errors:

                self.data["execution_time"][scenario_keys[0]][relative_error] = []
                self.data["num_required_runs"][scenario_keys[0]][relative_error] = []

                self.data["execution_time"][scenario_keys[1]][relative_error] = []
                self.data["num_required_runs"][scenario_keys[1]][relative_error] = []

                for j in xrange(self.num_iterations):
                    print "iteration:", j + 1
                    print "num_seed_runs:", self.num_seed_runs

                    # self.mca.test_classification_breaking_specified_link_sequence([('s2', 's1'), ('s4', 's1')], False)

                    with Timer(verbose=True) as t:
                        num_required_runs_uniform = self.compute_num_required_runs(self.expected_values[i],
                                                                                   float(relative_error),
                                                                                   "uniform",
                                                                                   2)

                    self.data["execution_time"][scenario_keys[0]][relative_error].append(t.msecs)
                    self.data["num_required_runs"][scenario_keys[0]][relative_error].append(num_required_runs_uniform)

                    with Timer(verbose=True) as t:
                        num_required_runs_importance = self.compute_num_required_runs(self.expected_values[i],
                                                                                      float(relative_error),
                                                                                      "importance",
                                                                                      2,
                                                                                      max(self.num_seed_runs,
                                                                                          self.num_seed_runs))

                    self.data["execution_time"][scenario_keys[1]][relative_error].append(t.msecs)
                    self.data["num_required_runs"][scenario_keys[1]][relative_error].append(num_required_runs_importance)

            self.mca.de_init_network_port_graph()

    def plot_monte_carlo(self, translate=False):

        if translate:

            if "num_required_runs" in self.data.keys():
                self.data["num_required_runs"]["Ring with uniform sampling"] = self.data["num_required_runs"]["ring_uniform"]
                self.data["num_required_runs"]["Ring with importance sampling"] = self.data["num_required_runs"]["ring_importance"]

                del self.data["num_required_runs"]["ring_uniform"]
                del self.data["num_required_runs"]["ring_importance"]

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
                                  xticks=[1, 5, 10], xtick_labels=["0.01", "0.05", "0.1"])

    def merge_load_data(self, filename_list):

        merged_data = {"execution_time": {}, "num_required_runs": {}}

        for filename in filename_list:

            print "Reading file:", filename

            with open(filename, "r") as infile:
                this_data = json.load(infile)

            merged_data["execution_time"].update(this_data["execution_time"])
            merged_data["num_required_runs"].update(this_data["num_required_runs"])

        self.data = merged_data


def main():

    #topo_descriptions = [("ring", 4, 1, None, None)]
    #topo_descriptions = [("ring", 6, 1, None, None)]
    #topo_descriptions = [("ring", 8, 1, None, None)]
    #topo_descriptions = [("ring", 10, 1, None, None)]

    #topo_descriptions = [("clostopo", None, 1, 2, 1)]
    #topo_descriptions = [("clostopo", None, 1, 2, 2)]

    #expected_values = [2.33]
    #expected_values = [2.5]
    #expected_values = [2.6]
    #expected_values = [2.77142857143]

    #expected_values = [5.00] # 5.15238302266
    #expected_values = [19.50]

    # topo_descriptions = [("ring", 4, 1, None, None),
    #                      ("ring", 6, 1, None, None),
    #                      ("ring", 8, 1, None, None),
    #                      ("ring", 10, 1, None, None)]
    #
    # expected_values = [2.33, 2.5, 2.16, 2.77142857143]

    network_configurations = [NetworkConfiguration("ryu",
                                                   "ring",
                                                   {"num_switches": 4,
                                                    "num_hosts_per_switch": 1},
                                                   load_config=False,
                                                   save_config=True,
                                                   synthesis_scheme="Synthesis_Failover_Aborescene")]

    num_iterations = 1
    num_seed_runs = 5
    relative_errors = ["10"]#,"1", "5", "10"]
    expected_values = [2.0]

    exp = MonteCarloSamplingCompare(network_configurations,
                                    num_iterations,
                                    num_seed_runs,
                                    relative_errors,
                                    expected_values)

    exp.trigger()
    exp.dump_data()

    # #Plot 4
    #exp.load_data("data/uniform_importance_sampling_compare_10_iterations_20160316_202014.json")

    # Plot 6
    #exp.load_data("data/uniform_importance_sampling_compare_10_iterations_20160331_133752.json")

    # Plot 8
    #exp.load_data("data/uniform_importance_sampling_compare_10_iterations_20160404_135504.json")

    # Merge plot.
    # exp.merge_load_data(["data/uniform_importance_sampling_compare_10_iterations_20160316_202014.json",
    #                      "data/uniform_importance_sampling_compare_10_iterations_20160331_133752.json",
    #                      "data/uniform_importance_sampling_compare_10_iterations_20160404_135504.json"])

    exp.plot_monte_carlo()

if __name__ == "__main__":
    main()
