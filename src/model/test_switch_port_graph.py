import unittest

from switch_port_graph import SwitchPortGraph
from network_graph import NetworkGraph
from experiments.network_configuration import NetworkConfiguration


class TestSwitchPortGraph(unittest.TestCase):

    def setUp(self):

        nc = NetworkConfiguration("ryu",
                                  "ring",
                                  {"num_switches": 4,
                                   "num_hosts_per_switch": 1},
                                  load_config=True,
                                  save_config=False,
                                  synthesis_scheme="Synthesis_Failover_Aborescene")

        ng = NetworkGraph(nc)
        sw = ng.get_node_object("s1")
        self.ring_swpg = SwitchPortGraph(ng, sw, True)
        sw.port_graph = self.ring_swpg
        self.ring_swpg.init_switch_port_graph()
        self.ring_swpg.compute_switch_admitted_traffic()

    def test_one_port_failure_at_a_time(self, verbose=False):

        test_passed = True

        # Loop over ports of the switch and fail and restore them one by one
        for testing_port_number in self.ring_swpg.sw.ports:

            print "testing_port_number:", testing_port_number

            testing_port = self.ring_swpg.sw.ports[testing_port_number]

            graph_paths_before = self.ring_swpg.get_graph_paths(verbose)
            graph_ats_before = self.ring_swpg.get_graph_ats()

            testing_port.state = "down"
            end_to_end_modified_edges = self.ring_swpg.update_admitted_traffic_due_to_port_state_change(testing_port_number,
                                                                                                   "port_down")

            graph_paths_intermediate = self.ring_swpg.get_graph_paths(verbose)
            graph_ats_intermediate = self.ring_swpg.get_graph_ats()

            testing_port.state = "up"
            end_to_end_modified_edges = self.ring_swpg.update_admitted_traffic_due_to_port_state_change(testing_port_number,
                                                                                                   "port_up")

            graph_paths_after = self.ring_swpg.get_graph_paths(verbose)
            graph_ats_after = self.ring_swpg.get_graph_ats()

            all_graph_paths_equal = self.ring_swpg.compare_graph_paths(graph_paths_before,
                                                                  graph_paths_after,
                                                                  verbose)

            if not all_graph_paths_equal:
                test_passed = all_graph_paths_equal
                print "Test Failed."

            all_graph_ats_equal = self.ring_swpg.compare_graph_ats(graph_ats_before,
                                                              graph_ats_after,
                                                              verbose)
            if not all_graph_ats_equal:
                test_passed = all_graph_ats_equal
                print "Test Failed."

        return test_passed

if __name__ == '__main__':
    unittest.main()
