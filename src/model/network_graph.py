__author__ = 'Rakesh Kumar'

import os
import time
import json
import httplib2
import networkx as nx

from collections import defaultdict

from switch import Switch
from host import Host
from flow_table import FlowTable
from group_table import GroupTable
from port import Port
from sel_controller import Session, OperationalTree, ConfigTree

class NetworkGraphLinkData():

    def __init__(self, node1_id, node1_port, node2_id, node2_port, link_type):
        self.link_ports_dict = {node1_id: node1_port, node2_id: node2_port}
        self.link_type = link_type


class NetworkGraph():

    def __init__(self, mm, controller, load_config=False, save_config=False):

        self.mm = mm

        self.OFPP_CONTROLLER = 0xfffffffd
        self.OFPP_ALL = 0xfffffffc
        self.OFPP_IN = 0xfffffff8
        self.OFPP_NORMAL = 0xfffffffa

        self.GROUP_FF = "group-ff"
        self.GROUP_ALL = "group-all"

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

        self.controller = controller

        self.config_path_prefix = "../experiments/configurations/" + self.controller + "_" + \
                                  self.mm.mininet_configuration_name + "/"

        if not os.path.exists(self.config_path_prefix):
            os.makedirs(self.config_path_prefix)

        self.load_config = load_config
        self.save_config = save_config

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
            # Get all the hosts and links from the topology API
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
            for sw in self.mm.topo.switches():
                mininet_host_nodes[sw] = []
                for h in self.mm.get_all_switch_hosts(sw):
                    mininet_host_dict = {"host_switch_id": "s" + sw[1:],
                                         "host_name": h.name,
                                         "host_IP": h.IP(),
                                         "host_MAC": h.MAC()}

                    mininet_host_nodes[sw].append(mininet_host_dict)

        if self.save_config:
            with open(self.config_path_prefix + "mininet_host_nodes.json", "w") as outfile:
                json.dump(mininet_host_nodes, outfile)

        return mininet_host_nodes

    def get_mininet_port_links(self):

        mininet_port_links = {}

        if self.load_config:
            with open(self.config_path_prefix + "mininet_port_links.json", "r") as in_file:
                mininet_port_links = json.loads(in_file.read())
        else:
            mininet_port_links = self.mm.topo.ports

        if self.save_config:
            with open(self.config_path_prefix + "mininet_port_links.json", "w") as outfile:
                json.dump(mininet_port_links, outfile)

        return mininet_port_links

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

    def parse_mininet_host_nodes(self, mininet_host_nodes, mininet_port_links):

        # From all the switches
        for sw in mininet_host_nodes:
            # For every host
            for mininet_host_dict in mininet_host_nodes[sw]:
                host_switch_obj = self.get_node_object(mininet_host_dict["host_switch_id"])

                # Add the host to the graph
                self.host_ids.append(mininet_host_dict["host_name"])
                sw_obj = self.get_node_object(sw)

                if self.load_config:
                    h_obj = Host(mininet_host_dict["host_name"],
                                 self,
                                 mininet_host_dict["host_IP"],
                                 mininet_host_dict["host_MAC"],
                                 mininet_host_dict["host_switch_id"],
                                 host_switch_obj,
                                 mininet_port_links[mininet_host_dict["host_name"]]['0'][1])

                    sw_obj.host_ports.append(mininet_port_links[mininet_host_dict["host_name"]]['0'][1])

                else:
                    h_obj = Host(mininet_host_dict["host_name"],
                                 self,
                                 mininet_host_dict["host_IP"],
                                 mininet_host_dict["host_MAC"],
                                 mininet_host_dict["host_switch_id"],
                                 host_switch_obj,
                                 mininet_port_links[mininet_host_dict["host_name"]][0][1])

                    sw_obj.host_ports.append(mininet_port_links[mininet_host_dict["host_name"]][0][1])

                self.graph.add_node(mininet_host_dict["host_name"], node_type="host", h=h_obj)

    def parse_mininet_port_links(self, mininet_port_links):

        for src_node in mininet_port_links:
            for src_node_port in mininet_port_links[src_node]:
                dst_list = mininet_port_links[src_node][src_node_port]
                dst_node = dst_list[0]
                dst_node_port = dst_list[1]

                self.add_link(src_node,
                              int(src_node_port),
                              dst_node,
                              int(dst_node_port))

    def parse_odl_node_links(self, topology):

        topology_links = dict()
        if "link" in topology["network-topology"]["topology"][0]:
            topology_links = topology["network-topology"]["topology"][0]["link"]

        for link in topology_links:

            # only add links for those nodes that are in the graph
            if link["source"]["source-node"] in self.graph.node and link["destination"]["dest-node"] in self.graph.node:

                if self.graph.node[link["source"]["source-node"]]["node_type"] == "switch":
                    node1_port = link["source"]["source-tp"].split(":")[2]
                else:
                    node1_port = "0"

                if self.graph.node[link["destination"]["dest-node"]]["node_type"] == "switch":
                    node2_port = link["destination"]["dest-tp"].split(":")[2]
                else:
                    node2_port = "0"

                self.add_link(link["source"]["source-node"], node1_port, link["destination"]["dest-node"], node2_port)

    def add_link(self, node1_id, node1_port, node2_id, node2_port):

        link_type = None

        if self.graph.node[node1_id]["node_type"] == "switch" and self.graph.node[node2_id]["node_type"] == "switch":
            link_type = "switch"
        elif self.graph.node[node1_id]["node_type"] == "host" and self.graph.node[node2_id]["node_type"] == "switch":
            link_type = "host"
        elif self.graph.node[node1_id]["node_type"] == "switch" and self.graph.node[node2_id]["node_type"] == "host":
            link_type = "host"
        else:
            raise Exception("Unknown Link Type")

        link_data = NetworkGraphLinkData(node1_id, node1_port, node2_id, node2_port, link_type)

        self.graph.add_edge(node1_id,
                            node2_id,
                            link_data=link_data)

        # Ensure that the ports are set up
        if self.graph.node[node1_id]["node_type"] == "switch":
            self.graph.node[node1_id]["sw"].ports[node1_port].state = "up"

        if self.graph.node[node2_id]["node_type"] == "switch":
            self.graph.node[node2_id]["sw"].ports[node2_port].state = "up"

    def remove_link(self, node1_id, node1_port, node2_id, node2_port):

        self.graph.remove_edge(node1_id, node2_id)

        if self.graph.node[node1_id]["node_type"] == "switch":
            self.graph.node[node1_id]["sw"].ports[node1_port].state = "down"

        if self.graph.node[node2_id]["node_type"] == "switch":
            self.graph.node[node2_id]["sw"].ports[node2_port].state = "down"

    def dump_model(self):

        print "Hosts in the graph:", self.host_ids
        print "Switches in the graph:", self.switch_ids
        print "Number of nodes in the graph:", self.graph.number_of_nodes()
        print "Number of links in the graph:", self.graph.number_of_edges()

        for sw in self.switch_ids:
            print "---", sw, "---"
            for port in self.graph.node[sw]["sw"].ports:
                print self.graph.node[sw]["sw"].ports[port]

    def get_ryu_switches(self):
        ryu_switches = {}
        request_gap = 0

        if self.load_config:

            with open(self.config_path_prefix + "ryu_switches.json", "r") as in_file:
                ryu_switches = json.loads(in_file.read())

        else:
            # Get all the ryu_switches from the inventory API
            remaining_url = 'stats/switches'
            time.sleep(request_gap)
            resp, content = self.h.request(self.baseUrlRyu + remaining_url, "GET")

            ryu_switch_numbers = json.loads(content)

            for dpid in ryu_switch_numbers:

                this_ryu_switch = {}

                # Get the flows
                remaining_url = 'stats/flow' + "/" + str(dpid)
                resp, content = self.h.request(self.baseUrlRyu + remaining_url, "GET")
                time.sleep(request_gap)

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
                time.sleep(request_gap)

                if resp["status"] == "200":
                    switch_ports = json.loads(content)
                    this_ryu_switch["ports"] = switch_ports[str(dpid)]
                else:
                    print "Error pulling switch ports from RYU."

                # Get the groups
                remaining_url = 'stats/groupdesc' + "/" + str(dpid)
                resp, content = self.h.request(self.baseUrlRyu + remaining_url, "GET")
                time.sleep(request_gap)

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
                if port["port_no"] == 4294967294:
                    continue

                switch_ports[int(port["port_no"])] = Port(sw, port_json=port)

            sw.ports = switch_ports

            # Parse group table if one is available
            if "groups" in ryu_switches[dpid]:
                sw.group_table = GroupTable(sw, ryu_switches[dpid]["groups"])

            # Parse all the flow tables and sort them by table_id in the list
            switch_flow_tables = []
            for table_id in ryu_switches[dpid]["flow_tables"]:
                switch_flow_tables.append(FlowTable(sw, table_id, ryu_switches[dpid]["flow_tables"][table_id]))
                sw.flow_tables = sorted(switch_flow_tables, key=lambda flow_table: flow_table.table_id)

    def print_sel_flow_stats(self):
       # for each in OperationalTree.flowStatsHttpAccess(self.sel_session).read_collection():
       for each in OperationalTree.FlowStatsEntityAccess(self.sel_session).read_collection():
            print (each.to_pyson())

    def get_sel_switches(self):
       # nodes = OperationalTree.nodesHttpAccess(self.sel_session)
        nodes = ConfigTree.NodesEntityAccess(self.sel_session)
        sel_switches = {}
        for each in nodes.read_collection():
            this_switch = {}
            if each.linked_key.startswith("OpenFlow"):
                switch_id = each.linked_key.split(':')[1]

                #ports = OperationalTree.portsHttpAccess(self.sel_session)
                ports = OperationalTree.PortsEntityAccess(self.sel_session)
                sw_ports = []

                for port in ports.read_collection():
                    if isinstance(port, OperationalTree.OpenFlowPort):
                        if port.parent_node == each.linked_key:
                            sw_ports.append(port.to_pyson())

                this_switch["ports"] = sw_ports

              #  groups = ConfigTree.groupsHttpAccess(self.sel_session)
                groups = ConfigTree.GroupsEntityAccess(self.sel_session)

                sw_groups = []
                for group in groups.read_collection():
                    if group.node == each.id:
                        sw_groups.append(group.to_pyson())

                this_switch["groups"] = sw_groups

                #flow_tables = ConfigTree.flowsHttpAccess(self.sel_session)
                flow_tables = ConfigTree.FlowsEntityAccess(self.sel_session)
                switch_flow_tables = defaultdict(list)
                for flow_rule in flow_tables.read_collection():
                    if flow_rule.node == each.id:
                        flow_rule = flow_rule.to_pyson()
                        switch_flow_tables[flow_rule["tableId"]].append(flow_rule)

                this_switch["flow_tables"] = switch_flow_tables

                sel_switches[switch_id] = this_switch

        if self.save_config:
            with open(self.config_path_prefix + "sel_switches.json", "w") as outfile:
                json.dump(sel_switches, outfile)

        return sel_switches

    def parse_sel_switches(self, sel_switches):
        for each_id, switch in sel_switches.iteritems():
            # prepare the switch id
            switch_id = "s" + str(each_id)

            sw = self.get_node_object(switch_id)
            # Check to see if a switch with this id already exists in the graph,
            # if so grab it, otherwise create it
            if not sw:
                sw = Switch(switch_id, self)
                self.graph.add_node(switch_id, node_type="switch", sw=sw)
                self.switch_ids.append(switch_id)
            # Parse out the information about all the ports in the switch
            switch_ports = {}
            for port in switch["ports"]:
                switch_ports[port["portId"]] = Port(sw, port_json=port)

            sw.ports = switch_ports

            # Parse group table if one is available
            if "groups" in sel_switches[each_id]:
                sw.group_table = GroupTable(sw, sel_switches[each_id]["groups"])

            # Parse all the flow tables and sort them by table_id in the list
            switch_flow_tables = []
            for table_id in sel_switches[each_id]["flow_tables"]:
                switch_flow_tables.append(FlowTable(sw, table_id,
                                                    sel_switches[each_id]["flow_tables"][table_id]))

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
        mininet_port_links = self.get_mininet_port_links()

        self.parse_mininet_host_nodes(mininet_host_nodes, mininet_port_links)
        self.parse_mininet_port_links(mininet_port_links)

        #self.dump_model()

    def get_node_graph(self):
        return self.graph

    def get_switches(self):
        for switch_id in self.switch_ids:
            yield self.get_node_object(switch_id)

    def get_link_ports_dict(self, node1_id, node2_id):
        link_data =  self.graph[node1_id][node2_id]['link_data']
        return link_data.link_ports_dict

    def get_switch_link_data(self):
        for edge in self.graph.edges_iter():
            link_data =  self.graph[edge[0]][edge[1]]['link_data']
            if link_data.link_type == "switch":
                yield link_data


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

    def get_num_rules(self):

        num_rules = 0

        for sw in self.get_switches():
            for flow_table in sw.flow_tables:
                num_rules += len(flow_table.flows)

        return num_rules

def main():
    m = NetworkGraph()

if __name__ == "__main__":
    main()
