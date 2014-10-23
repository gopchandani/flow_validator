import requests 
from create_xml import create_group, create_flow_rule_group, create_simple_flow_rule
from create_url import create_group_url, create_flow_url

header = {'Content-Type':'application/xml', 'Accept':'application/xml'}

# creates group
# two actions, 
create_group(id_group='4',action1='7',action2='6', filename='group.xml')

# node_id = switch_id
group_url = create_group_url(node_id='1', group_id='4')

#creates flow forwarding to group
create_flow_rule_group(id_flow="11", id_table="0", id_group="4", src_ip='10.0.0.9', dst_ip='10.0.0.2', priority="10", 
	filename="groupflow.xml")

flow_group_url = create_flow_url(node_id='1',table_id='0',flow_id='11')

# creates flow forwarding to outport
create_simple_flow_rule(id_flow="12", id_table="0", out_port="2", src_ip='10.0.0.1', dst_ip='10.0.0.2', priority="10", 
	filename="simple.xml")
flow_url = create_flow_url(node_id='1',table_id='0',flow_id='12')


r = requests.put(group_url, data=open('group.xml', 'rb'), auth=('admin', 'admin'), headers=header)
print(r.text)
r = requests.put(flow_group_url, data=open('groupflow.xml', 'rb'), auth=('admin', 'admin'), headers=header)
print(r.text)
r = requests.put(flow_url, data=open('simple.xml', 'rb'), auth=('admin', 'admin'), headers=header)
print(r.text)
