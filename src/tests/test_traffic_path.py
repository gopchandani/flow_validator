import unittest
import os

from model.traffic import Traffic
from model.network_port_graph import NetworkPortGraph
from experiments.network_configuration import NetworkConfiguration


class TestTrafficPath(unittest.TestCase):

    @classmethod
    def attach_hosts_port_nodes_with_npg(cls, ng, npg):

        # Attach a destination port for each host.
        for host_id in ng.host_ids:

            host_obj = ng.get_node_object(host_id)
            host_obj.switch_ingress_port = npg.get_node(host_obj.switch_id +
                                                        ":ingress" +
                                                        str(host_obj.switch_port_attached))
            host_obj.switch_egress_port = npg.get_node(host_obj.switch_id +
                                                       ":egress" +
                                                       str(host_obj.switch_port_attached))
    @classmethod
    def init_hosts_traffic_propagation(cls, ng, npg):
        for host_id in ng.host_ids:
            host_obj = ng.get_node_object(host_id)

            dst_traffic_at_succ = Traffic(init_wildcard=True)
            dst_traffic_at_succ.set_field("ethernet_type", 0x0800)
            dst_mac_int = int(host_obj.mac_addr.replace(":", ""), 16)
            dst_traffic_at_succ.set_field("ethernet_destination", dst_mac_int)

            print "Initializing for host:", host_id

            end_to_end_modified_edges = []

            npg.propagate_admitted_traffic(host_obj.switch_egress_port,
                                           dst_traffic_at_succ,
                                           None,
                                           host_obj.switch_egress_port,
                                           end_to_end_modified_edges)

    @classmethod
    def setUpClass(cls):

        cls.nc_ring_aborescene_apply_true = NetworkConfiguration("ryu",
                                                                 "ring",
                                                                 {"num_switches": 4,
                                                                  "num_hosts_per_switch": 1},
                                                                 conf_root=os.path.dirname(__file__) + "/",
                                                                 synthesis_name="AboresceneSynthesis",
                                                                 synthesis_params={"apply_group_intents_immediately":
                                                                                       True})

        cls.ng_ring_aborescene_apply_true = cls.nc_ring_aborescene_apply_true.setup_network_graph(mininet_setup_gap=1,
                                                                                                  synthesis_setup_gap=1)
        cls.npg_ring_aborescene_apply_true = NetworkPortGraph(cls.ng_ring_aborescene_apply_true, False)
        cls.npg_ring_aborescene_apply_true.init_network_port_graph()

        cls.attach_hosts_port_nodes_with_npg(cls.ng_ring_aborescene_apply_true, cls.npg_ring_aborescene_apply_true)
        cls.init_hosts_traffic_propagation(cls.ng_ring_aborescene_apply_true, cls.npg_ring_aborescene_apply_true)

        cls.nc_clos_dijkstra = NetworkConfiguration("ryu",
                                                    "clostopo",
                                                    {"fanout": 2,
                                                     "core": 1,
                                                     "num_hosts_per_switch": 1},
                                                    conf_root=os.path.dirname(__file__) + "/",
                                                    synthesis_name="DijkstraSynthesis",
                                                    synthesis_params={})

        cls.ng_clos_dijkstra = cls.nc_clos_dijkstra.setup_network_graph(mininet_setup_gap=1,
                                                                        synthesis_setup_gap=1)
        cls.npg_clos_dijkstra = NetworkPortGraph(cls.ng_clos_dijkstra, False)
        cls.npg_clos_dijkstra.init_network_port_graph()

        cls.attach_hosts_port_nodes_with_npg(cls.ng_clos_dijkstra, cls.npg_clos_dijkstra)
        cls.init_hosts_traffic_propagation(cls.ng_clos_dijkstra, cls.npg_clos_dijkstra)

    def check_get_succs_with_admitted_traffic_and_vuln_rank(self):
        pass

    def test_ring_aborescene_get_succs_with_admitted_traffic_and_vuln_rank(self):
        pass


if __name__ == '__main__':
    unittest.main()
