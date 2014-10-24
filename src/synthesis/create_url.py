def create_group_url(node_id,  group_id):
	return 'http://localhost:8181/restconf/config/opendaylight-inventory:nodes/node/'+str(node_id)+'/group/'+str(group_id)

def create_flow_url(node_id, table_id, flow_id):
	return 'http://localhost:8181/restconf/config/opendaylight-inventory:nodes/node/'+str(node_id)+'/table/'+str(table_id)+'/flow/'+str(flow_id)

