__author__ = 'Rakesh Kumar'

import json
import httplib2
import networkx as nx

from switch import Switch
from host import Host
from flow_table import FlowTable
from group_table import GroupTable
from port import Port

class NetworkGraph():

    def __init__(self, mininet_man=None, load_config=False, save_config=False):

        self.mininet_man = mininet_man

        self.OFPP_CONTROLLER = 0xfffffffd
        self.OFPP_ALL = 0xfffffffc
        self.OFPP_IN = 0xfffffff8

        # Initialize the self.graph
        self.graph = nx.Graph()

        # Initialize things to talk to controller
        self.baseUrl = 'http://localhost:8181/restconf/'
        self.h = httplib2.Http(".cache")
        self.h.add_credentials('admin', 'admin')

        # Initialize lists of host and switch ids
        self.host_ids = []
        self.switch_ids = []

        self.load_config = load_config
        self.save_config = save_config

        #  Load up everything
        self._parse_network_graph()

    def _get_odl_switches(self):

        switches = {}
        group_tables = {}

        if self.load_config:

            with open("../experiments/configurations/switches.json", "r") as in_file:
                switches = json.loads(in_file.read())

            with open("../experiments/configurations/group_tables.json", "r") as in_file:
                group_tables = json.loads(in_file.read())

        else:
            # Get all the switches from the inventory API
            remaining_url = 'operational/opendaylight-inventory:nodes'
            resp, content = self.h.request(self.baseUrl + remaining_url, "GET")
            switches = json.loads(content)

            #  Go through each node and grab the switches and the corresponding hosts associated with the switch
            for node in switches["nodes"]["node"]:

                #  Add an instance for Switch in the graph
                switch_id = node["id"]
                remaining_url = "config/opendaylight-inventory:nodes/node/" + str(switch_id)
                resp, content = self.h.request(self.baseUrl + remaining_url, "GET")

                if resp["status"] == "200":
                    switch_node = json.loads(content)

                    if "flow-node-inventory:group" in switch_node['node'][0]:
                        group_tables[node["id"]] = switch_node['node'][0]["flow-node-inventory:group"]


        if self.save_config:
            with open("../experiments/configurations/switches.json", "w") as outfile:
                json.dump(switches, outfile)

            with open("../experiments/configurations/group_tables.json", "w") as outfile:
                json.dump(group_tables, outfile)

        return switches, group_tables

    def _get_odl_topology(self):

        topology = {}

        if self.load_config:
            with open("../experiments/configurations/topology.json", "r") as in_file:
                topology = json.loads(in_file.read())
        else:
            # Get all the hosts and edges from the topology API
            remaining_url = 'operational/network-topology:network-topology'
            resp, content = self.h.request(self.baseUrl + remaining_url, "GET")
            topology = json.loads(content)

        if self.save_config:
            with open("../experiments/configurations/topology.json", "w") as outfile:
                json.dump(topology, outfile)

        return topology

    def _get_mininet_host_nodes_edges(self):

        mininet_switch_hosts_dict = {}
        mininet_topo_ports = {}

        if self.load_config:
            with open("../experiments/configurations/mininet_switch_hosts_dict.json", "r") as in_file:
                mininet_switch_hosts_dict = json.loads(in_file.read())
            with open("../experiments/configurations/mininet_topo_ports.json", "r") as in_file:
                mininet_topo_ports = json.loads(in_file.read())
        else:
            for sw in self.mininet_man.topo.switch_names:
                mininet_switch_hosts_dict[sw] = []
                for h in self.mininet_man.get_switch_hosts(sw):
                    mininet_host_dict = {"host_switch_id": "openflow:" + sw[1:],
                                         "host_name": h.name,
                                         "host_IP": h.IP(),
                                         "host_MAC": h.MAC()}

                    mininet_switch_hosts_dict[sw].append(mininet_host_dict)

            mininet_topo_ports = self.mininet_man.topo.ports

        if self.save_config:
            with open("../experiments/configurations/mininet_switch_hosts_dict.json", "w") as outfile:
                json.dump(mininet_switch_hosts_dict, outfile)
            with open("../experiments/configurations/mininet_topo_ports.json", "w") as outfile:
                json.dump(mininet_topo_ports, outfile)

        return mininet_switch_hosts_dict, mininet_topo_ports

    def parse_odl_switches(self, switches, group_tables):

        #  Go through each node and grab the switches and the corresponding hosts associated with the switch
        for node in switches["nodes"]["node"]:

            #  Add an instance for Switch in the graph
            switch_id = node["id"]
            sw = Switch(switch_id, self)
            self.graph.add_node(switch_id, node_type="switch", sw=sw)
            self.switch_ids.append(switch_id)

            #  Get the ports
            switch_ports = {}

            # Parse out the information about all the ports in the switch
            for nc in node["node-connector"]:
                if nc["flow-node-inventory:port-number"] != "LOCAL":
                    switch_ports[nc["flow-node-inventory:port-number"]] = Port(sw, nc)
            sw.ports = switch_ports

            #  Get the group table
            if switch_id in group_tables:
                sw.group_table = GroupTable(sw, group_tables[switch_id])

            #  Get all the flow tables
            switch_flow_tables = []
            for flow_table in node["flow-node-inventory:table"]:
                if "flow" in flow_table:
                    switch_flow_tables.append(FlowTable(sw, flow_table["id"], flow_table["flow"]))

            #  Set the flow tables in the object instance while sorting them
            sw.flow_tables = sorted(switch_flow_tables, key=lambda flow_table: flow_table.table_id)

    def _parse_odl_host_nodes(self, topology):

        topology_nodes = dict()
        if "node" in topology["network-topology"]["topology"][0]:
            topology_nodes = topology["network-topology"]["topology"][0]["node"]

        # Extract all hosts in the topology
        for node in topology_nodes:
            if node["node-id"].startswith("host"):
                host_id = node["node-id"]
                host_ip = node["host-tracker-service:addresses"][0]["ip"]
                host_mac = node["host-tracker-service:addresses"][0]["mac"]

                switch_attachment_point = node["host-tracker-service:attachment-points"][0]["tp-id"].split(":")
                host_switch_id = switch_attachment_point[0] + ":" + switch_attachment_point[1]
                host_switch_obj = self.get_node_object(host_switch_id)

                self.host_ids.append(host_id)
                h = Host(host_id, self, host_ip, host_mac, host_switch_id, host_switch_obj, switch_attachment_point[2])
                self.graph.add_node(host_id, node_type="host", h=h)

    def _parse_mininet_host_nodes_edges(self, mininet_switch_hosts_dict, mininet_topo_ports):

        # From all the switches
        for sw in mininet_switch_hosts_dict:
            # For every host
            for mininet_host_dict in mininet_switch_hosts_dict[sw]:
                host_switch_obj = self.get_node_object(mininet_host_dict["host_switch_id"])

                # Add the host to the graph
                self.host_ids.append(mininet_host_dict["host_name"])
                h_obj = Host(mininet_host_dict["host_name"],
                             self,
                             mininet_host_dict["host_IP"],
                             mininet_host_dict["host_MAC"],
                             mininet_host_dict["host_switch_id"],
                             host_switch_obj,
                             str(mininet_topo_ports[mininet_host_dict["host_name"]]['0'][1]))

                self.graph.add_node(mininet_host_dict["host_name"], node_type="host", h=h_obj)

                # Add the edge from host to switch
                self.add_edge(mininet_host_dict["host_name"],
                              str(0),
                              mininet_host_dict["host_switch_id"],
                              str(mininet_topo_ports[mininet_host_dict["host_name"]]['0'][1]))

    def _parse_odl_node_edges(self, topology):

        topology_links = dict()
        if "link" in topology["network-topology"]["topology"][0]:
            topology_links = topology["network-topology"]["topology"][0]["link"]

        for link in topology_links:

            # only add edges for those nodes that are in the graph
            if link["source"]["source-node"] in self.graph.node and link["destination"]["dest-node"] in self.graph.node:

                if self.graph.node[link["source"]["source-node"]]["node_type"] == "switch":
                    node1_port = link["source"]["source-tp"].split(":")[2]
                else:
                    node1_port = "0"

                if self.graph.node[link["destination"]["dest-node"]]["node_type"] == "switch":
                    node2_port = link["destination"]["dest-tp"].split(":")[2]
                else:
                    node2_port = "0"

                self.add_edge(link["source"]["source-node"], node1_port, link["destination"]["dest-node"], node2_port)

    def add_edge(self, node1_id, node1_port, node2_id, node2_port):

        edge_port_dict = {node1_id: node1_port, node2_id: node2_port}
        #print "Adding edge:", edge_port_dict

        e = (node1_id, node2_id)
        self.graph.add_edge(*e, edge_ports_dict=edge_port_dict)
        # Ensure that the ports are set up

        if self.graph.node[node1_id]["node_type"] == "switch":
            self.graph.node[node1_id]["sw"].ports[node1_port].state = "up"

        if self.graph.node[node2_id]["node_type"] == "switch":
            self.graph.node[node2_id]["sw"].ports[node2_port].state = "up"

    def remove_edge(self, node1_id, node1_port, node2_id, node2_port):

        #TODO: Not really need to remove it
        self.graph.remove_edge(node1_id, node2_id)

        if self.graph.node[node1_id]["node_type"] == "switch":
            self.graph.node[node1_id]["sw"].ports[node1_port].state = "down"

        if self.graph.node[node2_id]["node_type"] == "switch":
            self.graph.node[node2_id]["sw"].ports[node2_port].state = "down"

    def get_edge_port_dict(self, node1_id, node2_id):
        return self.graph[node1_id][node2_id]['edge_ports_dict']

    def dump_model(self):

        print "Hosts in the graph:", self.host_ids
        print "Switches in the graph:", self.switch_ids
        print "Number of nodes in the graph:", self.graph.number_of_nodes()
        print "Number of edges in the graph:", self.graph.number_of_edges()

        for sw in self.switch_ids:
            print "---", sw, "---"
            for port in self.graph.node[sw]["sw"].ports:
                print self.graph.node[sw]["sw"].ports[port]

    def _parse_network_graph(self):

        switches, group_tables = self._get_odl_switches()
        self.parse_odl_switches(switches, group_tables)

        topology = self._get_odl_topology()

        if not self.mininet_man:
            self._parse_odl_host_nodes(topology)
        else:
            mininet_switch_hosts_dict, mininet_topo_ports = self._get_mininet_host_nodes_edges()
            self._parse_mininet_host_nodes_edges(mininet_switch_hosts_dict, mininet_topo_ports)

        self._parse_odl_node_edges(topology)

        #self.dump_model()

    def get_node_graph(self):
        return self.graph

    def get_host_ids(self):
        return self.host_ids

    def get_hosts(self):
        for host_id in self.host_ids:
            yield self.get_node_object(host_id)

    def get_switch_ids(self):
        return self.switch_ids

    def get_switches(self):
        for switch_id in self.switch_ids:
            yield self.get_node_object(switch_id)

    def get_host_id_node_with_ip(self, req_ip):
        host_node_id = None

        for host_id in self.get_host_ids():

            if self.graph.node[host_id]["h"].ip_addr == req_ip:
                host_node_id = host_id
                break

        return host_node_id

    def get_node_object(self, node_id):
        node_obj = None

        if self.graph.has_node(node_id):

            graph_node = self.graph.node[node_id]
            if graph_node["node_type"] == "switch":
                node_obj = graph_node["sw"]

            elif graph_node["node_type"] == "host":
                node_obj = graph_node["h"]

        return node_obj

    def get_node_type(self, node_id):
        node_type = None

        if self.graph.has_node(node_id):
            node_type = self.graph.node[node_id]["node_type"]

        return node_type

def main():

    m = NetworkGraph()

if __name__ == "__main__":
    main()
