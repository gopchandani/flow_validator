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

    def __init__(self):

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

        #  Load up everything
        self._load_model()

    def _prepare_group_table(self, sw):

        group_table = None
        node_id = sw.node_id

        # Get all the nodes/switches from the inventory API
        remaining_url = 'config/opendaylight-inventory:nodes/node/' + str(node_id)

        resp, content = self.h.request(self.baseUrl + remaining_url, "GET")

        if resp["status"] == "200":
            node = json.loads(content)

            if "flow-node-inventory:group" in node["node"][0]:
                groups_json = node["node"][0]["flow-node-inventory:group"]
                group_table = GroupTable(sw, groups_json)

            else:
                print "No groups configured in node:", node_id
        else:
#            print "Could not fetch any groups via the API, status:", resp["status"]
            pass
        return group_table

    def _prepare_switch_nodes(self):

        # Get all the nodes/switches from the inventory API
        remaining_url = 'operational/opendaylight-inventory:nodes'

        resp, content = self.h.request(self.baseUrl + remaining_url, "GET")
        nodes = json.loads(content)

        #  Go through each node and grab the switches and the corresponding hosts associated with the switch
        for node in nodes["nodes"]["node"]:

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
            switch_group_table = self._prepare_group_table(sw)
            sw.group_table = switch_group_table

            #  Get all the flow tables
            switch_flow_tables = []
            for flow_table in node["flow-node-inventory:table"]:
                if "flow" in flow_table:
                    switch_flow_tables.append(FlowTable(sw, flow_table["id"], flow_table["flow"]))

            #  Set the flow tables in the object instance while sorting them
            sw.flow_tables = sorted(switch_flow_tables, key=lambda flow_table: flow_table.table_id)



    def add_edge(self, node1_id, node1_port, node2_id, node2_port):

        edge_port_dict = {node1_id: node1_port, node2_id: node2_port}

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

    def simulate_add_edge(self, node1_id, node2_id):

        edge_ports_dict = self.get_edge_port_dict(node1_id, node2_id)

        node1_port = edge_ports_dict[node1_id]
        node2_port = edge_ports_dict[node2_id]

        if self.graph.node[node1_id]["node_type"] == "switch":
            self.graph.node[node1_id]["sw"].ports[node1_port].state = "up"

        if self.graph.node[node2_id]["node_type"] == "switch":
            self.graph.node[node2_id]["sw"].ports[node2_port].state = "up"


    def simulate_remove_edge(self, node1_id, node2_id):

        edge_ports_dict = self.get_edge_port_dict(node1_id, node2_id)

        node1_port = edge_ports_dict[node1_id]
        node2_port = edge_ports_dict[node2_id]

        if self.graph.node[node1_id]["node_type"] == "switch":
            self.graph.node[node1_id]["sw"].ports[node1_port].state = "down"

        if self.graph.node[node2_id]["node_type"] == "switch":
            self.graph.node[node2_id]["sw"].ports[node2_port].state = "down"



    def get_edge_port_dict(self, node1_id, node2_id):
        return self.graph[node1_id][node2_id]['edge_ports_dict']

    def _prepare_node_edges(self):

        # Go through the topology API
        remaining_url = 'operational/network-topology:network-topology'
        resp, content = self.h.request(self.baseUrl + remaining_url, "GET")
        topology = json.loads(content)

        topology_links = dict()
        if "link" in topology["network-topology"]["topology"][0]:
            topology_links = topology["network-topology"]["topology"][0]["link"]

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

        for link in topology_links:

            if self.graph.node[link["source"]["source-node"]]["node_type"] == "switch":
                node1_port = link["source"]["source-tp"].split(":")[2]
            else:
                node1_port = "0"

            if self.graph.node[link["destination"]["dest-node"]]["node_type"] == "switch":
                node2_port = link["destination"]["dest-tp"].split(":")[2]
            else:
                node2_port = "0"


            self.add_edge(link["source"]["source-node"], node1_port, link["destination"]["dest-node"], node2_port)

            if self.graph.node[link["source"]["source-node"]]["node_type"] == "switch":
                node1_ports = self.graph.node[link["source"]["source-node"]]["sw"].ports

                if not node1_ports[node1_port].faces:
                    node1_ports[node1_port].faces = self.graph.node[link["destination"]["dest-node"]]["node_type"]

                if not node1_ports[node1_port].facing_node_id:
                    node1_ports[node1_port].facing_node_id = link["destination"]["dest-node"]

            if self.graph.node[link["destination"]["dest-node"]]["node_type"] == "switch":
                node2_ports = self.graph.node[link["destination"]["dest-node"]]["sw"].ports

                if not node2_ports[node2_port].faces:
                    node2_ports[node2_port].faces = self.graph.node[link["source"]["source-node"]]["node_type"]

                if not node2_ports[node2_port].facing_node_id:
                    node2_ports[node2_port].facing_node_id = link["source"]["source-node"]

    def dump_model(self):

        print "Hosts in the graph:", self.host_ids
        print "Switches in the graph:", self.switch_ids
        print "Number of nodes in the graph:", self.graph.number_of_nodes()
        print "Number of edges in the graph:", self.graph.number_of_edges()

        for sw in self.switch_ids:
            print "---", sw, "---"
            for port in self.graph.node[sw]["sw"].ports:
                print self.graph.node[sw]["sw"].ports[port]

    def _load_model(self):

        self._prepare_switch_nodes()
        self._prepare_node_edges()

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