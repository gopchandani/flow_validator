__author__ = 'Rakesh Kumar'

import json

import httplib2
import networkx as nx


class ODL_Model():
    def __init__(self):

        # Initialize the self.graph
        self.graph = nx.Graph()

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

        # Get all the flow statistics
        resp, content = h.request(baseUrl + 'statistics/' + containerName + 'flow', "GET")
        flowStatistics = json.loads(content)
        flowStatistics = flowStatistics["flowStatistics"]
        for fs in flowStatistics:
            import pprint

            pprint.pprint(fs["node"])
            for flow in fs["flowStatistic"]:
                pprint.pprint(flow["flow"]["match"])
                pprint.pprint(flow["flow"]["actions"])
                pprint.pprint(flow["flow"]["priority"])

        # Put switches in the graph
        for node in odlNodes:
            self.graph.add_node(node['node']['id'])

        #  Put all the edges between switches
        for edge in odlEdges:
            e = (edge['edge']['headNodeConnector']['node']['id'], edge['edge']['tailNodeConnector']['node']['id'])
            self.graph.add_edge(*e)

        #  Put hosts in the graph and the relevant edges
        for host in hosts:
            self.graph.add_node(host['networkAddress'])
            e = (host['networkAddress'], host['nodeId'])
            self.graph.add_edge(*e)

    def get_node_graph(self):
        return self.graph
