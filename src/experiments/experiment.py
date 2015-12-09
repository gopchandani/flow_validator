__author__ = 'Rakesh Kumar'

import pdb
import json
import time
import numpy as np
import scipy.stats as ss

from pprint import pprint
from controller_man import ControllerMan
from mininet_man import MininetMan
from model.network_graph import NetworkGraph
from sel_controller import adopt_all

class Experiment(object):

    def __init__(self,
                 experiment_name,
                 num_iterations,
                 load_config,
                 save_config,
                 controller,
                 experiment_switches,
                 num_controller_instances):

        self.experiment_tag = experiment_name + "_" +time.strftime("%Y%m%d_%H%M%S")

        self.num_iterations = num_iterations
        self.load_config = load_config
        self.save_config = save_config
        self.controller = controller
        self.experiment_switches = experiment_switches
        self.num_controller_instances = num_controller_instances

        self.data = {}

        self.controller_port = 6633
        self.cm = None
        if not self.load_config and self.save_config:
            self.cm = ControllerMan(self.num_controller_instances, controller=controller)

    def setup_network_graph(self, topo_description, qos=False):

        if not self.load_config and self.save_config:
            self.controller_port = self.cm.get_next()

        controller_host = None
        # TODO(abhilash)
        # Hard coding the port for now, need to remove this later.
        if self.controller == "sel":
            self.controller_port = 6653
            controller_host = "192.168.56.1"
        self.mm = MininetMan(self.controller_port, controller_host, *topo_description)

        if self.controller == "sel":
            time.sleep(5)
            print("Trying to adopt all hosts on {0}:{1}".format(controller_host, 1234))
            adopt_all.main("http://selcontroller:1234/")
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
                if qos:
                    self.mm.setup_mininet_with_ryu_qos(ng)
                else:
                    self.mm.setup_mininet_with_ryu(ng)
            elif self.controller == "sel":
                self.mm.setup_mininet_with_sel(ng)

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
