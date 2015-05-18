__author__ = 'Rakesh Kumar'


import json
import time
import numpy as np
import scipy.stats as ss

from pprint import pprint
from controller_man import ControllerMan
from mininet_man import MininetMan
from model.network_graph import NetworkGraph

class Experiment(object):

    def __init__(self,
                 experiment_name,
                 num_iterations,
                 load_config,
                 save_config,
                 controller,
                 experiment_switches):

        self.experiment_tag = experiment_name + "_" +time.strftime("%Y%m%d_%H%M%S")

        self.num_iterations = num_iterations
        self.load_config = load_config
        self.save_config = save_config
        self.controller = controller
        self.experiment_switches = experiment_switches

        self.data = {}

    def setup_network_graph(self, topo_description):

        self.controller_port = 6633

        if not self.load_config and self.save_config:
            cm = ControllerMan(1, controller=self.controller)
            controller_port = cm.get_next()

        self.mm = MininetMan(self.controller_port, *topo_description)

        # Get a flow validator instance
        ng = NetworkGraph(mininet_man=self.mm,
                          controller=self.controller,
                          experiment_switches=self.experiment_switches,
                          save_config=self.save_config,
                          load_config=self.load_config)

        if not self.load_config and self.save_config:
            if self.controller == "odl":
                self.mm.setup_mininet_with_odl(ng)
            elif self.controller == "ryu":
                #self.mm.setup_mininet_with_ryu_router()
                #self.mm.setup_mininet_with_ryu_qos(ng)
                self.mm.setup_mininet_with_ryu(ng)

        # Refresh the network_graph
        ng.parse_switches()

        return ng

    def dump_data(self):
        pprint(self.data)
        filename = "data/" + self.experiment_tag + "_data.json"
        print "Writing to file:", filename

        with open(filename, "w") as outfile:
            json.dump(self.data, outfile)

    def get_x_y_err(self, data_dict):

        x = sorted(data_dict.keys())

        data_means = []
        data_sems = []

        for p in x:
            mean = np.mean(data_dict[p])
            sem = ss.sem(data_dict[p])
            data_means.append(mean)
            data_sems.append(sem)

        return x, data_means, data_sems
