__author__ = 'Rakesh Kumar'

import json

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
        baseUrl = 'http://localhost:8080/controller/nb/v2/'
        containerName = 'default/'
        h = httplib2.Http(".cache")
        h.add_credentials('admin', 'admin')

        # Get all the edges/links
        resp, content = h.request(baseUrl + 'topology/' + containerName, "GET")
        edgeProperties = json.loads(content)
        odlEdges = edgeProperties['edgeProperties']

        # Get all the nodes/switches
        resp, content = h.request(baseUrl + 'switchmanager/' + containerName + 'nodes/', "GET")
        nodeProperties = json.loads(content)
        odlNodes = nodeProperties['nodeProperties']

        # Get all the active hosts
        resp, content = h.request(baseUrl + 'hosttracker/' + containerName + 'hosts/active', "GET")
        hostProperties = json.loads(content)
        hosts = hostProperties["hostConfig"]

        # Get all the flow statistics and construct rules from them
        resp, content = h.request(baseUrl + 'statistics/' + containerName + 'flow', "GET")
        flowStatistics = json.loads(content)
        flowStatistics = flowStatistics["flowStatistics"]
        for fs in flowStatistics:
            flow_table = FlowTable(fs)

        # Put switches in the graph
        for node in odlNodes:
            self.switch_ids.append(node['node']['id'])
            self.graph.add_node(node['node']['id'], type="switch")

        #  Put all the edges between switches
        for edge in odlEdges:
            e = (edge['edge']['headNodeConnector']['node']['id'], edge['edge']['tailNodeConnector']['node']['id'])
            self.graph.add_edge(*e)

        #  Put hosts in the graph and the relevant edges
        for host in hosts:
            self.graph.add_node(host['networkAddress'], type="host")
            self.host_ids.append(host['networkAddress'])
            e = (host['networkAddress'], host['nodeId'])
            self.graph.add_edge(*e)

    def get_node_graph(self):
        return self.graph

    def get_host_ids(self):
        return self.host_ids

    def get_switch_ids(self):
        return self.switch_ids
