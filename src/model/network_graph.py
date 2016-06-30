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


class NetworkGraphLinkData(object):

    def __init__(self, node1_id, node1_port, node2_id, node2_port, link_type):
        self.link_ports_dict = {str(node1_id): node1_port, str(node2_id): node2_port}
        self.link_type = link_type
        self.traffic_paths = []
        self.causes_disconnect = None

        self.forward_port_graph_edge = (str(node1_id) + ':' + "egress" + str(node1_port),
                                        str(node2_id) + ':' + "ingress" + str(node2_port))

        self.reverse_port_graph_edge = (str(node2_id) + ':' + "egress" + str(node2_port),
                                        str(node1_id) + ':' + "ingress" + str(node1_port))

        self.forward_link = (str(node1_id), str(node2_id))
        self.reverse_link = (str(node2_id), str(node1_id))

    def __str__(self):
        return str(self.forward_link)


class NetworkGraph(object):

    def __init__(self, network_configuration):

        self.network_configuration = network_configuration
        self.total_flow_rules = 0

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

        self.controller = self.network_configuration.controller

        # Load up everything
        self.parse_network_graph()

    # Gets a switch-only multi-di-graph for the present topology
    def get_mdg(self):

        mdg = nx.MultiDiGraph(self.graph)

        for n in self.graph:
            node_type = self.get_node_type(n)

            # Remove all host nodes
            if node_type == "host":
                mdg.remove_node(n)

        return mdg

    def get_mininet_host_nodes(self):

        mininet_host_nodes = {}

        if self.network_configuration.load_config:
            with open(self.network_configuration.conf_path + "mininet_host_nodes.json", "r") as in_file:
                mininet_host_nodes = json.loads(in_file.read())
        else:
            for sw in self.network_configuration.topo.switches():
                mininet_host_nodes[sw] = []
                for h in self.network_configuration.get_all_switch_hosts(sw):
                    mininet_host_dict = {"host_switch_id": "s" + sw[1:],
                                         "host_name": h.name,
                                         "host_IP": h.IP(),
                                         "host_MAC": h.MAC()}

                    mininet_host_nodes[sw].append(mininet_host_dict)

        if self.network_configuration.save_config:
            with open(self.network_configuration.conf_path + "mininet_host_nodes.json", "w") as outfile:
                json.dump(mininet_host_nodes, outfile)

        return mininet_host_nodes

    def get_mininet_port_links(self):

        mininet_port_links = {}

        if self.network_configuration.load_config:
            with open(self.network_configuration.conf_path + "mininet_port_links.json", "r") as in_file:
                mininet_port_links = json.loads(in_file.read())
        else:
            mininet_port_links = self.network_configuration.topo.ports

        if self.network_configuration.save_config:
            with open(self.network_configuration.conf_path + "mininet_port_links.json", "w") as outfile:
                json.dump(mininet_port_links, outfile)

        return mininet_port_links

    def parse_mininet_host_nodes(self, mininet_host_nodes, mininet_port_links):

        # From all the switches
        for sw in mininet_host_nodes:
            # For every host
            for mininet_host_dict in mininet_host_nodes[sw]:
                host_switch_obj = self.get_node_object(mininet_host_dict["host_switch_id"])

                # Add the host to the graph
                self.host_ids.append(mininet_host_dict["host_name"])
                sw_obj = self.get_node_object(sw)

                if self.network_configuration.load_config:
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

    def get_ryu_switches(self):
        ryu_switches = {}
        request_gap = 0

        if self.network_configuration.load_config:
            with open(self.network_configuration.conf_path + "ryu_switches.json", "r") as in_file:
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

        if self.network_configuration.save_config:
            with open(self.network_configuration.conf_path + "ryu_switches.json", "w") as outfile:
                json.dump(ryu_switches, outfile)

        return ryu_switches

    def parse_ryu_switches(self, ryu_switches):

        #  Go through each node and grab the ryu_switches and the corresponding hosts associated with the switch
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

                if port["port_no"] == "LOCAL":
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

        if self.network_configuration.save_config:
            with open(self.network_configuration.conf_path + "sel_switches.json", "w") as outfile:
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

    def parse_network_graph(self):

        self.total_flow_rules = 0

        if self.network_configuration.controller == "odl":
            raise NotImplemented

        elif self.network_configuration.controller == "ryu":
            ryu_switches = self.get_ryu_switches()
            self.parse_ryu_switches(ryu_switches)

        mininet_host_nodes = self.get_mininet_host_nodes()
        mininet_port_links = self.get_mininet_port_links()

        self.parse_mininet_host_nodes(mininet_host_nodes, mininet_port_links)
        self.parse_mininet_port_links(mininet_port_links)

    def get_node_graph(self):
        return self.graph

    def get_switches(self):
        for switch_id in self.switch_ids:
            yield self.get_node_object(switch_id)

    def get_link_ports_dict(self, node1_id, node2_id):
        link_data =  self.graph[node1_id][node2_id]['link_data']
        return link_data.link_ports_dict

    def get_link_data(self, node1_id, node2_id):
        link_data =  self.graph[node1_id][node2_id]['link_data']
        return link_data

    def get_switch_link_data(self):
        for edge in self.graph.edges():
            link_data =  self.graph[edge[0]][edge[1]]['link_data']
            if link_data.link_type == "switch":
                yield link_data

    def get_adjacent_switch_link_data(self, switch_id):
        for link_data in self.get_switch_link_data():
            if switch_id in link_data.link_ports_dict:

                adjacent_sw_id = None
                if switch_id == link_data.forward_link[0]:
                    adjacent_sw_id = link_data.forward_link[1]
                else:
                    adjacent_sw_id = link_data.forward_link[0]

                yield adjacent_sw_id, link_data

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
