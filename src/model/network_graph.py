__author__ = 'Rakesh Kumar'

import os
import json
import httplib2
import networkx as nx

from collections import defaultdict

from switch import Switch
from host import Host
from flow_table import FlowTable
from group_table import GroupTable
from port import Port

class NetworkGraph():

    def __init__(self, mininet_man, controller, experiment_switches, load_config=False, save_config=False, ):

        self.mininet_man = mininet_man

        self.OFPP_CONTROLLER = 0xfffffffd
        self.OFPP_ALL = 0xfffffffc
        self.OFPP_IN = 0xfffffff8
        self.OFPP_NORMAL = 0xfffffffa

        # Initialize the self.graph
        self.graph = nx.Graph()

        # Initialize things to talk to controller
        self.baseUrlOdl = "http://localhost:8181/restconf/"
        self.baseUrlRyu = "http://localhost:8080/"

        self.h = httplib2.Http(".cache")
        self.h.add_credentials('admin', 'admin')

        # Initialize lists of host and switch ids
        self.host_ids = []
        self.switch_ids = []

        self.experiment_switches = experiment_switches

        dir_name = str(self.mininet_man.topo_name) + str(self.mininet_man.num_switches) + str(self.mininet_man.num_hosts_per_switch)
        self.config_path_prefix = "../experiments/configurations/" + dir_name + "/"

        if not os.path.exists(self.config_path_prefix):
            os.makedirs(self.config_path_prefix)

        self.load_config = load_config
        self.save_config = save_config
        self.controller = controller

        #  Load up everything
        self.parse_network_graph()

    def get_odl_switches(self):

        odl_switches = {}

        if self.load_config:

            with open(self.config_path_prefix + "odl_switches.json", "r") as in_file:
                odl_switches = json.loads(in_file.read())

        else:
            # Get all the odl_switches from the inventory API
            remaining_url = 'operational/opendaylight-inventory:nodes'
            resp, content = self.h.request(self.baseUrlOdl + remaining_url, "GET")
            odl_switches = json.loads(content)

            # Grab each switch's group table with a separate GET request
            for node in odl_switches["nodes"]["node"]:

                #  Add an instance for Switch in the graph
                remaining_url = "config/opendaylight-inventory:nodes/node/" + str(node["id"])
                resp, content = self.h.request(self.baseUrlOdl + remaining_url, "GET")

                if resp["status"] == "200":
                    switch_node = json.loads(content)

                    if "flow-node-inventory:group" in switch_node['node'][0]:
                        node["flow-node-inventory:group"] = switch_node['node'][0]["flow-node-inventory:group"]

        if self.save_config:
            with open(self.config_path_prefix + "odl_switches.json", "w") as outfile:
                json.dump(odl_switches, outfile)

        return odl_switches

    def get_odl_topology(self):

        topology = {}

        if self.load_config:
            with open(self.config_path_prefix + "topology.json", "r") as in_file:
                topology = json.loads(in_file.read())
        else:
            # Get all the hosts and edges from the topology API
            remaining_url = 'operational/network-topology:network-topology'
            resp, content = self.h.request(self.baseUrlOdl + remaining_url, "GET")
            topology = json.loads(content)

        if self.save_config:
            with open(self.config_path_prefix + "topology.json", "w") as outfile:
                json.dump(topology, outfile)

        return topology

    def get_mininet_host_nodes(self):

        mininet_host_nodes = {}

        if self.load_config:
            with open(self.config_path_prefix + "mininet_host_nodes.json", "r") as in_file:
                mininet_host_nodes = json.loads(in_file.read())
        else:
            for sw in self.mininet_man.topo.switches():
                mininet_host_nodes[sw] = []
                for h in self.mininet_man.get_all_switch_hosts(sw):
                    mininet_host_dict = {"host_switch_id": "s" + sw[1:],
                                         "host_name": h.name,
                                         "host_IP": h.IP(),
                                         "host_MAC": h.MAC()}

                    mininet_host_nodes[sw].append(mininet_host_dict)

        if self.save_config:
            with open(self.config_path_prefix + "mininet_host_nodes.json", "w") as outfile:
                json.dump(mininet_host_nodes, outfile)

        return mininet_host_nodes

    def get_mininet_port_edges(self):

        mininet_port_edges = {}

        if self.load_config:
            with open(self.config_path_prefix + "mininet_port_edges.json", "r") as in_file:
                mininet_port_edges = json.loads(in_file.read())
        else:
            mininet_port_edges = self.mininet_man.topo.ports

        if self.save_config:
            with open(self.config_path_prefix + "mininet_port_edges.json", "w") as outfile:
                json.dump(mininet_port_edges, outfile)

        return mininet_port_edges

    def parse_odl_switches(self, odl_switches):

        #  Go through each node and grab the odl_switches and the corresponding hosts associated with the switch
        for node in odl_switches["nodes"]["node"]:

            #  prepare a switch id
            switch_id = "s" + node["id"].split(":")[1]

            # Check to see if a switch with this id already exists in the graph,
            # if so grab it, otherwise create it

            sw = self.get_node_object(switch_id)
            if not sw:
                sw = Switch(switch_id, self)
                self.graph.add_node(switch_id, node_type="switch", sw=sw)
                self.switch_ids.append(switch_id)

            # Parse out the information about all the ports in the switch
            switch_ports = {}
            for nc in node["node-connector"]:
                if nc["flow-node-inventory:port-number"] != "LOCAL":
                    switch_ports[int(nc["flow-node-inventory:port-number"])] = Port(sw, port_json=nc)
            sw.ports = switch_ports

            # Parse group table if one is available
            if "flow-node-inventory:group" in node:
                sw.group_table = GroupTable(sw, node["flow-node-inventory:group"])

            # Parse all the flow tables and sort them by table_id in the list
            switch_flow_tables = []
            for flow_table in node["flow-node-inventory:table"]:
                if "flow" in flow_table:
                    switch_flow_tables.append(FlowTable(sw, flow_table["id"], flow_table["flow"]))
            sw.flow_tables = sorted(switch_flow_tables, key=lambda flow_table: flow_table.table_id)


    def parse_mininet_host_nodes(self, mininet_host_nodes, mininet_port_edges):

        # From all the switches
        for sw in mininet_host_nodes:
            # For every host
            for mininet_host_dict in mininet_host_nodes[sw]:
                host_switch_obj = self.get_node_object(mininet_host_dict["host_switch_id"])

                # Add the host to the graph
                self.host_ids.append(mininet_host_dict["host_name"])

                if self.load_config:
                    h_obj = Host(mininet_host_dict["host_name"],
                                 self,
                                 mininet_host_dict["host_IP"],
                                 mininet_host_dict["host_MAC"],
                                 mininet_host_dict["host_switch_id"],
                                 host_switch_obj,
                                 mininet_port_edges[mininet_host_dict["host_name"]]['0'][1])
                else:
                    h_obj = Host(mininet_host_dict["host_name"],
                                 self,
                                 mininet_host_dict["host_IP"],
                                 mininet_host_dict["host_MAC"],
                                 mininet_host_dict["host_switch_id"],
                                 host_switch_obj,
                                 mininet_port_edges[mininet_host_dict["host_name"]][0][1])

                self.graph.add_node(mininet_host_dict["host_name"], node_type="host", h=h_obj)


    def parse_mininet_port_edges(self, mininet_port_edges):

        for src_node in mininet_port_edges:
            for src_node_port in mininet_port_edges[src_node]:
                dst_list = mininet_port_edges[src_node][src_node_port]
                dst_node = dst_list[0]
                dst_node_port = dst_list[1]

                self.add_edge(src_node,
                              int(src_node_port),
                              dst_node,
                              int(dst_node_port))

    def parse_odl_node_edges(self, topology):

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

        self.graph.add_edge(node1_id,
                            node2_id,
                            edge_ports_dict={node1_id: node1_port,
                                             node2_id: node2_port})

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

    def get_ryu_switches(self):
        ryu_switches = {}

        if self.load_config:

            with open(self.config_path_prefix + "ryu_switches.json", "r") as in_file:
                ryu_switches = json.loads(in_file.read())

        else:
            # Get all the ryu_switches from the inventory API
            remaining_url = 'stats/switches'
            resp, content = self.h.request(self.baseUrlRyu + remaining_url, "GET")

            ryu_switch_numbers = json.loads(content)

            for dpid in ryu_switch_numbers:

                this_ryu_switch = {}

                # Get the flows
                remaining_url = 'stats/flow' + "/" + str(dpid)
                resp, content = self.h.request(self.baseUrlRyu + remaining_url, "GET")

                if resp["status"] == "200":
                    switch_flows = json.loads(content)
                    switch_flow_tables = defaultdict(list)
                    for flow_rule in switch_flows[str(dpid)]:
                        switch_flow_tables[flow_rule["table_id"]].append(flow_rule)
                    this_ryu_switch["flow_tables"] = switch_flow_tables
                else:
                    print "Error pulling switch flows from RYU."

                # Get the ports
                remaining_url = 'stats/portdesc' + "/" + str(dpid)
                resp, content = self.h.request(self.baseUrlRyu + remaining_url, "GET")

                if resp["status"] == "200":
                    switch_ports = json.loads(content)
                    this_ryu_switch["ports"] = switch_ports[str(dpid)]
                else:
                    print "Error pulling switch ports from RYU."

                # Get the groups
                remaining_url = 'stats/group' + "/" + str(dpid)
                resp, content = self.h.request(self.baseUrlRyu + remaining_url, "GET")

                if resp["status"] == "200":
                    switch_groups = json.loads(content)
                    this_ryu_switch["groups"] = switch_groups[str(dpid)]
                else:
                    print "Error pulling switch ports from RYU."

                ryu_switches[dpid] = this_ryu_switch

        if self.save_config:
            with open(self.config_path_prefix + "ryu_switches.json", "w") as outfile:
                json.dump(ryu_switches, outfile)

        return ryu_switches

    def parse_ryu_switches(self, ryu_switches):

        #  Go through each node and grab the odl_switches and the corresponding hosts associated with the switch
        for dpid in ryu_switches:

            #  prepare a switch id
            switch_id = "s" + str(dpid)

            # Check to see if a switch with this id already exists in the graph,
            # if so grab it, otherwise create it
            sw = self.get_node_object(switch_id)
            if not sw:
                sw = Switch(switch_id, self)
                self.graph.add_node(switch_id, node_type="switch", sw=sw)
                self.switch_ids.append(switch_id)

            # Parse out the information about all the ports in the switch
            switch_ports = {}
            for port in ryu_switches[dpid]["ports"]:
                switch_ports[int(port["port_no"])] = Port(sw, port_json=port)

            sw.ports = switch_ports

            # Parse group table if one is available
            #if ryu_switches[dpid]["groups"]:
                #sw.group_table = GroupTable(sw, node["flow-node-inventory:group"])

            # Parse all the flow tables and sort them by table_id in the list

            if switch_id == "s3":
                pass

            switch_flow_tables = []
            for table_id in ryu_switches[dpid]["flow_tables"]:
                switch_flow_tables.append(FlowTable(sw, table_id, ryu_switches[dpid]["flow_tables"][table_id]))
                sw.flow_tables = sorted(switch_flow_tables, key=lambda flow_table: flow_table.table_id)


    def parse_switches(self):
        
        if self.controller == "odl":
            odl_switches = self.get_odl_switches()
            self.parse_odl_switches(odl_switches)
            
        elif self.controller == "ryu":
            ryu_switches = self.get_ryu_switches()
            self.parse_ryu_switches(ryu_switches)

    def parse_network_graph(self):
        
        self.parse_switches()

        mininet_host_nodes = self.get_mininet_host_nodes()
        mininet_port_edges = self.get_mininet_port_edges()

        self.parse_mininet_host_nodes(mininet_host_nodes, mininet_port_edges)
        self.parse_mininet_port_edges(mininet_port_edges)

        #self.dump_model()

    def get_node_graph(self):
        return self.graph

    def get_experiment_host_ids(self):

        switch_host_ids = []

        for host_id in self.host_ids:
            host_obj = self.get_node_object(host_id)
            if host_obj.switch_id in self.experiment_switches:
                switch_host_ids.append(host_id)

        return switch_host_ids

    def get_hosts(self):
        for host_id in self.host_ids:

            host_obj = self.get_node_object(host_id)
            if host_obj.switch_id in self.experiment_switches:
                yield host_obj
            else:
                return

    def get_switch_ids(self):
        return self.switch_ids

    def get_switches(self):
        for switch_id in self.switch_ids:
            yield self.get_node_object(switch_id)

    def get_host_id_node_with_ip(self, req_ip):
        host_node_id = None

        for host_id in self.get_experiment_host_ids():

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
