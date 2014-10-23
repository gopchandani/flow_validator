import requests 
from create_xml import create_group, create_flow_rule_group, create_simple_flow_rule
from create_url import create_group_url, create_flow_url

header = {'Content-Type':'application/xml', 'Accept':'application/xml'}

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