import requests 
# from create_xml import create_group, create_flow_rule_group, create_simple_flow_rule, create_flow_with_inport
# from create_url import create_group_url, create_flow_url
from model.model import Model
import networkx as nx


header = {'Content-Type':'application/xml', 'Accept':'application/xml'}


class Tester:
# link = get_link[node_id-1][node_id-2] info
# link.node_id_1 link.node_id_1	
	def __init__(self):
		self.flow_id = 10	
		self.model = Model()
		self.graph = self.model.get_node_graph()
		self.host_ids = self.model.get_host_ids()
		self.switch_ids = self.model.get_switch_ids()

	def test(self):
		
		# returns link where link is {node_id1:port_on_node_id1,node_id2:port_on_node_id2}		
		# print self.graph.number_of_nodes()
		# print self.graph.number_of_edges()
				
		print self.switch_ids
		print self.host_ids
		print self.graph.nodes()
		paths = nx.all_simple_paths(self.graph,source=self.host_ids[0], target=self.host_ids[1])
		for path in paths:
			link = self.graph[self.host_ids[0]][path[1]]
			print link['edge_ports_dict'][path[1]]
			print path
		print link
		return 
	
	# returns the path between h1 and h2 
def main():
	t = Tester()
	t.test()

if __name__ == "__main__":
	main()