__author__ = 'Rakesh Kumar'

import json
import sys
import pprint

import httplib2
import networkx as nx

from flow_table import FlowTable


class Model():
    def __init__(self):

        # Initialize the self.graph
        self.graph = nx.Graph()

        # Initialize lists of host and switch ids
        self.host_ids = []
        self.switch_ids = []

        #  Load up everything
        self._load_model()


    def _load_model(self):
        #http://localhost:8181/restconf/operational/opendaylight-inventory:nodes
        #http://localhost:8181/restconf/config/opendaylight-inventory:nodes/node/openflow:1

        baseUrl = 'http://localhost:8181/restconf/'
        h = httplib2.Http(".cache")
        h.add_credentials('admin', 'admin')

        # Get all the nodes/switches from the inventory API
        remaining_url = 'operational/opendaylight-inventory:nodes'

        resp, content = h.request(baseUrl + remaining_url, "GET")
        nodes = json.loads(content)


        #  Go through each node and grab the switches and the corresponding hosts associated with the switch
        for node in nodes["nodes"]["node"]:

            switch_id = node["id"]
            switch_flow_tables = []

            # Parse out the flow tables in the switch
            for flow_table in node["flow-node-inventory:table"]:
                #  Only capture those flow_tables that have actual rules in them
                if "flow" in flow_table:
                    switch_flow_tables.append(FlowTable(flow_table["id"], flow_table["flow"]))

            # Add the switch node
            self.switch_ids.append(switch_id)
            self.graph.add_node(switch_id, type="switch", flow_tables= switch_flow_tables)

            #  For all things that are connected to this switch...
            for node_connector in node["node-connector"]:

                #  If the node connector points to a host
                if "address-tracker:addresses" in node_connector:
                    host_id =  node_connector["address-tracker:addresses"][0]["ip"]
                    switch_port = node_connector["flow-node-inventory:port-number"]

                    self.graph.add_node(host_id, type="host")
                    self.host_ids.append(host_id)

                    e = (host_id, switch_id)

                    # It is unknown which host port the wire between switch and host is connected on
                    edgePorts = {host_id: None, switch_id: switch_port}
                    self.graph.add_edge(*e, edge_ports_dict=edgePorts)


        #TODO: Put all the edges between switches

        # Go through the topology API
        remaining_url = 'operational/network-topology:network-topology'
        resp, content = h.request(baseUrl + remaining_url, "GET")
        topology = json.loads(content)
        topology_links = topology["network-topology"]["topology"][0]["link"]

        for link in topology_links:
            node1 = link["source"]["source-node"]
            node2 = link["destination"]["dest-node"]

            node1_port = link["source"]["source-tp"].split(":")[2]
            node2_port = link["destination"]["dest-tp"].split(":")[2]

            edge_port_dict = {node1: node1_port, node2: node2_port}
            e = (node1, node2)
            self.graph.add_edge(*e, edge_ports_dict=edge_port_dict)

        #print len(topology_links)
        #print self.graph.number_of_nodes()
        #print self.graph.number_of_edges()

    def get_node_graph(self):
        return self.graph

    def get_host_ids(self):
        return self.host_ids

    def get_switch_ids(self):
        return self.switch_ids



def main():
    m = Model()
    m._load_model()


if __name__ == "__main__":
    main()
