import xml.etree.cElementTree as ET

# writes xml for group creation
def create_group(id_group, action1, action2, filename):
	root = ET.Element('group')
	root.set('xmlns', "urn:opendaylight:flow:inventory")
	
	group_type = ET.SubElement(root, 'group-type')
	group_type.text = "group-ff"

	buckets = ET.SubElement(root, 'buckets')

	bucket = ET.SubElement(buckets, 'bucket')

	action = ET.SubElement(bucket, 'action')

	order = ET.SubElement(action, 'order')
	order.text = "0"

	output_action = ET.SubElement(action, 'output-action')
	output_node_connector = ET.SubElement(output_action, 'output-node-connector' )
	output_node_connector.text = action1

	bucket_id = ET.SubElement(bucket, 'bucket-id')
	bucket_id.text = '1'
	
	watch_port = ET.SubElement(bucket, "watch_port")
	watch_port.text = action1

	weight = ET.SubElement(bucket, 'weight')
	weight.text = '20'
	# 
	
	bucket_two = ET.SubElement(buckets, 'bucket')
	action_two = ET.SubElement(bucket_two, 'action')
	order_two = ET.SubElement(action_two, 'order')
	order_two.text = '1'

	output_action2 = ET.SubElement(action_two,'output-action')
	output_node_connector2 = ET.SubElement(output_action2, 'output-node-connector')
	output_node_connector2.text = action2
	
	bucket_id2 = ET.SubElement(bucket_two, 'bucket-id')
	bucket_id2.text = '2'
	
	watch_port2 = ET.SubElement(bucket_two, 'watch_port')
	watch_port2.text = action2
	weight2 = ET.SubElement(bucket_two, 'weight')
	weight2.text = '20'
	# 
	barrier = ET.SubElement(root, 'barrier')
	barrier.text = 'false'

	group_id = ET.SubElement(root, 'group-id')
	group_id.text = id_group

	tree = ET.ElementTree(root)
	tree.write(filename, encoding='utf-8', xml_declaration=True)

# writes xml for simple flow thats sends packet on out_port
def create_simple_flow_rule(id_flow, id_table, out_port, src_ip, dst_ip, priority, filename):
	
	root = ET.Element("flow")
	root.set("xmlns","urn:opendaylight:flow:inventory")

	strict = ET.SubElement(root, "strict")
	strict.text = "false"

	flow_id = ET.SubElement(root, "id")
	flow_id.text = id_flow
	
	priority_field = ET.SubElement(root, 'priority')
	priority_field.text = priority
	
	cookie_mask = ET.SubElement(root, "cookie_mask")
	cookie_mask.text = "255"

	cookie = ET.SubElement(root, "cookie")
	cookie.text = "103"

	table_id = ET.SubElement(root, "table_id")
	table_id.text = id_table

	hard_timeout = ET.SubElement(root, "hard-timeout")
	hard_timeout.text = "0"

	idle_timeout = ET.SubElement(root, "idle-timeout")
	idle_timeout.text = "0"


	installHw = ET.SubElement(root, "installHw")
	installHw.text = "false"

	instructions = ET.SubElement(root, "instructions")
	instruction = ET.SubElement(instructions, "instruction")
	order = ET.SubElement(instruction, "order")
	order.text = "0"

	apply_actions = ET.SubElement(instruction, "apply-actions")
	action = ET.SubElement(apply_actions, "action")

	order_action = ET.SubElement(action, "order")
	order_action.text = "0"

	output_action = ET.SubElement(action, "output-action")

	output_node_connector = ET.SubElement(output_action, "output-node-connector")
	output_node_connector.text = out_port



	match = ET.SubElement(root, 'match')

	ethernet_match = ET.SubElement(match, 'ethernet-match')
	ethernet_type = ET.SubElement(ethernet_match, 'ethernet-type')
	type_number = ET.SubElement(ethernet_type,'type')
	type_number.text = "2048"

	ip_src = ET.SubElement(match, 'ipv4-source')
	ip_src.text = src_ip

	ip_dst = ET.SubElement(match, 'ipv4-destination')
	ip_dst.text = dst_ip

	tree = ET.ElementTree(root)
	tree.write(filename, encoding='utf-8', xml_declaration=True)

# writes xml for flow that sends packet for processing to group
def create_flow_rule_group(id_flow, id_table, id_group, src_ip, dst_ip, priority, filename):
	
	root = ET.Element("flow")
	root.set("xmlns","urn:opendaylight:flow:inventory")

	strict = ET.SubElement(root, "strict")
	strict.text = "false"

	flow_id = ET.SubElement(root, "id")
	flow_id.text = id_flow

	priority_field = ET.SubElement(root, 'priority')
	priority_field.text = priority

	cookie_mask = ET.SubElement(root, "cookie_mask")
	cookie_mask.text = "255"

	cookie = ET.SubElement(root, "cookie")
	cookie.text = "103"

	table_id = ET.SubElement(root, "table_id")
	table_id.text = id_table

	hard_timeout = ET.SubElement(root, "hard-timeout")
	hard_timeout.text = "0"

	idle_timeout = ET.SubElement(root, "idle-timeout")
	idle_timeout.text = "0"


	installHw = ET.SubElement(root, "installHw")
	installHw.text = "false"

	instructions = ET.SubElement(root, "instructions")
	instruction = ET.SubElement(instructions, "instruction")
	order = ET.SubElement(instruction, "order")
	order.text = "0"

	apply_actions = ET.SubElement(instruction, "apply-actions")
	action = ET.SubElement(apply_actions, "action")

	order_action = ET.SubElement(action, "order")
	order_action.text = "0"

	group_action = ET.SubElement(action, "group-action")

	group_id = ET.SubElement(group_action, "group-id")
	group_id.text = id_group

	match = ET.SubElement(root, 'match')

	ethernet_match = ET.SubElement(match, 'ethernet-match')
	ethernet_type = ET.SubElement(ethernet_match, 'ethernet-type')
	type_number = ET.SubElement(ethernet_type,'type')
	type_number.text = "2048"

	ip_src = ET.SubElement(match, 'ipv4-source')
	ip_src.text = src_ip

	ip_dst = ET.SubElement(match, 'ipv4-destination')
	ip_dst.text = dst_ip

	tree = ET.ElementTree(root)
	tree.write(filename, encoding='utf-8', xml_declaration=True)

# create_flow_rule_group(id_flow="10", id_table="0", id_group="3", src_ip='10.0.0.5', dst_ip='10.0.0.2', priority="10", 
# 	filename="groupflow.xml")

# create_simple_flow_rule(id_flow="1", id_table="0", out_port="2", src_ip='10.0.0.1', dst_ip='10.0.0.2', priority="10", 
# 	filename="simple.xml")

# create_group(id_group='3',action1='5',action2='6', filename='group.xml')