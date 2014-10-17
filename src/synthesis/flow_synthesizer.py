import requests 
from create_xml import create_group, create_flow_rule_group, create_simple_flow_rule, create_flow_with_inport
from create_url import create_group_url, create_flow_url
from model.model import Model
import networkx as nx

class Flow_Synthesizer:

# link = get_link[node_id-1][node_id-2] info
# link.node_id_1 link.node_id_1
	def __init__(self):
		self.model() = Model()
		self.flow_id = 10
		self.group_id = 1
		self.table_id = '0'
		self.priority = '101'
		self.priority_down_link_break = '102'
		self.header = {'Content-Type':'application/xml', 'Accept':'application/xml'}

		self.model = Model()
		self.graph = self.model.get_node_graph()
		self.host_ids = self.model.get_host_ids()
		self.switch_ids = self.model.get_switch_ids()

	def get_link(self, node_id1, node_id2):
		# returns link where link is {node_id1:port_on_node_id1,node_id2:port_on_node_id2}		
		
		return link
	
	# returns the path between h1 and h2 
	def get_path(self, src, dst):
		# returns the paths. where paths {0:shortest_path_list, 1:backup_path_list}
		
		return nx.all_simple_paths(self.graph,source=src, target=dst)

	
	def install_simple_flow(self, h, node_id):
		# get host node link and add simple flow.
		# host_node_link = get_link(h1, paths[0][0])
		
		# create_simple_flow_rule(id_flow=str(self.flow_id), id_table=self.table_id, out_port="1", src_ip='10.0.0.3', dst_ip='10.0.0.2', priority="102", 
	# filename="simple.xml")
	
	# create rule that install group at node_id and actions are node_id->node_to_connect1,node_to_connect2 
	def install_group_and_flow(self, src, dst, node_id, node_to_connect1, node_to_connect2):

	def install_handle_failure_down_path(self, src, dst, node_reciever, node_sender):

	def install_path(self, src, dst):
		
		paths = self.get_path(src, dst)

		# get host-node link and install flow
		# first node in both paths 
		len_path1 = len(paths[0])
		len_path2 = len(paths[1])
		
		# host_node_link = get_link(src, paths[0][0])
		
		# installs rule at edge switch to forward packet to host
		
		# self.install_simple_flow(h=src, node_id=paths[0][0])
		
		self.install_simple_flow(h=dst, node_id=paths[0][len_path1 - 1])

		#create group and install flow at edge node (node connected to h1)
		self.install_group_and_flow(src=src, dst=dst, node_id=paths[0][0], node_to_connect1=paths[0][1],node_to_connect2=paths[1][1])


		# add group and flow values on nodes on shortest path
		for i in range(1,len_path1):
			self.install_group_and_flow(src=src, dst=dst, node_id=paths[0][i], node_to_connect1=paths[0][i-1],node_to_connect2=paths[0][i+1])

		for i in range(1, len_path2):
			self.install_group_and_flow(src=src, dst=dst, node_id=paths[1][i], node_to_connect1=paths[1][i-1],node_to_connect2=paths[1][i+1])

		# rules added to handle returning traffic due to failure down the link.
		if (len_path1 > 2): 
			for i in range(0, len_path1 - 2):
				# add higher priority rule to handle packets coming due to failure down the path
				self.install_handle_failure_down_path(src=src, dst=dst, node_reciever=paths[0][i], node_sender=paths[0][i+1])

		if (len_path2 > 2):
			for i in range(0, len_path1 - 2):
				# add higher priority rule to handle packets coming due to failure down the path
				self.install_handle_failure_down_path(src=src, dst=dst, node_reciever=paths[1][i], node_sender=paths[1][i+1])
		













############################################################
#rules for s1

# creates group
create_group(id_group='2',action1='3',action2='2', filename='group.xml')
group_url = create_group_url(node_id='1', group_id='2')

#creates flow forwarding to group
create_flow_rule_group(id_flow="20", id_table="0", id_group="2", src_ip='10.0.0.2', dst_ip='10.0.0.3', priority="102", 
	filename="groupflow.xml")
flow_group_url = create_flow_url(node_id='1',table_id='0',flow_id='20')

# creates flow forwarding to outport
create_simple_flow_rule(id_flow="21", id_table="0", out_port="1", src_ip='10.0.0.3', dst_ip='10.0.0.2', priority="102", 
	filename="simple.xml")
flow_url = create_flow_url(node_id='1',table_id='0',flow_id='21')

r = requests.put(group_url, data=open('group.xml', 'rb'), auth=('admin', 'admin'), headers=header)
print(r.text)
r = requests.put(flow_group_url, data=open('groupflow.xml', 'rb'), auth=('admin', 'admin'), headers=header)
print(r.text)
r = requests.put(flow_url, data=open('simple.xml', 'rb'), auth=('admin', 'admin'), headers=header)
print(r.text)
#############################################################
#flows for node_id = 2

# creates group
create_group(id_group='2',action1='2',action2='3', filename='group.xml')
group_url = create_group_url(node_id='2', group_id='2')

#creates flow forwarding to group
create_flow_rule_group(id_flow="20", id_table="0", id_group="2", src_ip='10.0.0.3', dst_ip='10.0.0.2', priority="102", 
	filename="groupflow.xml")
flow_group_url = create_flow_url(node_id='2',table_id='0',flow_id='20')

# creates flow forwarding to outport
create_simple_flow_rule(id_flow="21", id_table="0", out_port="1", src_ip='10.0.0.2', dst_ip='10.0.0.3', priority="102", 
	filename="simple.xml")
flow_url = create_flow_url(node_id='2',table_id='0',flow_id='21')


r = requests.put(group_url, data=open('group.xml', 'rb'), auth=('admin', 'admin'), headers=header)
print(r.text)
r = requests.put(flow_group_url, data=open('groupflow.xml', 'rb'), auth=('admin', 'admin'), headers=header)
print(r.text)
r = requests.put(flow_url, data=open('simple.xml', 'rb'), auth=('admin', 'admin'), headers=header)
print(r.text)

########################################
# rules for node_id = 51151578793544

# creates flow forwarding to outport
# create_simple_flow_rule(id_flow="1", id_table="0", out_port="2", src_ip='10.0.0.3', dst_ip='10.0.0.2', priority="102", 
# 	filename="simple1.xml")
# flow_url1 = create_flow_url(node_id='51151578793544',table_id='0',flow_id='1')

# create_simple_flow_rule(id_flow="2", id_table="0", out_port="3", src_ip='10.0.0.2', dst_ip='10.0.0.3', priority="102", 
# 	filename="simple2.xml")
# flow_url2 = create_flow_url(node_id='51151578793544',table_id='0',flow_id='2')

# r = requests.put(flow_url1, data=open('simple1.xml', 'rb'), auth=('admin', 'admin'), headers=header)
# print(r.text)
# r = requests.put(flow_url2, data=open('simple2.xml', 'rb'), auth=('admin', 'admin'), headers=header)
# print(r.text)