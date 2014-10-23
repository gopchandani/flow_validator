def create_group_url(node_id,  group_id):
	return 'http://localhost:8181/restconf/config/opendaylight-inventory:nodes/node/'+node_id+'/group/'+group_id

def create_flow_url(node_id, table_id, flow_id):
	return 'http://localhost:8181/restconf/config/opendaylight-inventory:nodes/node/'+node_id+'/table/'+table_id+'/flow/'+flow_id

