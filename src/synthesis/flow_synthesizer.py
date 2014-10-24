import requests 
from create_xml import create_group, create_flow_rule_group, create_simple_flow_rule, create_flow_with_inport
from create_url import create_group_url, create_flow_url
from model.model import Model
import networkx as nx
import time

class Flow_Synthesizer:

# link = get_link[node_id-1][node_id-2] info
# link.node_id_1 link.node_id_1
    def __init__(self):
        self.flow_id = 100
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
        # returns link
        link = self.graph[node_id1][node_id2]
        return link['edge_ports_dict']


    # returns the path between h1 and h2
    def get_path(self, src, dst):
        # returns the paths with only switcehs
        paths = []
        path_gen = nx.all_simple_paths(self.graph,source=src, target=dst)
        for path in path_gen:
            path.remove(src)
            path.remove(dst)
            paths.append(path)
            print 'path:', path
        return paths

    def install_simple_flow(self, src, dst, node_id):
        # need to get link from dst-node_id
        print 'In install_simple_flow'
        print 'src:', src
        print 'dst:', dst
        print 'node_id:', node_id
        link = self.get_link(dst, node_id)
        print 'switch_port:', link[node_id]

        create_simple_flow_rule(id_flow=str(self.flow_id), id_table=self.table_id, out_port=link[node_id], src_ip=src, dst_ip=dst, priority=self.priority, filename="simple.xml")
        url = create_flow_url(node_id=node_id, table_id=self.table_id, flow_id=str(self.flow_id))
        r = requests.put(url, data=open('simple.xml', 'rb'), auth=('admin', 'admin'), headers=self.header)
        print(r.text)
        self.flow_id+=1

    # create rule that install group at node_id and actions are node_id->node_to_connect1,node_to_connect2
    def install_group_and_flow(self, src, dst, node_id, node_to_connect1, node_to_connect2, return_flag):
        link1 = self.get_link(node_id, node_to_connect1)
        action_port1 = link1[node_id]

        link2 = self.get_link(node_id, node_to_connect2)

        if return_flag is True:
            action_port2 = '4294967288'
        else:
            action_port2 = link2[node_id]

        watch_port2 = link2[node_id]

        print 'In install_group_and_flow '
        print 'node_id:', node_id
        print 'action_port1:', action_port1
        print 'action_port2:', action_port2
        print 'watch_port2:', watch_port2

        create_group(id_group=str(self.group_id), action1=action_port1 , action2=action_port2, watchport2=watch_port2, filename='group.xml')
        group_url = create_group_url(node_id=node_id, group_id=str(self.group_id))

        create_flow_rule_group(id_flow=str(self.flow_id), id_table=self.table_id, id_group=str(self.group_id), src_ip=src, dst_ip=dst, priority=self.priority, filename="groupflow.xml")
        flow_group_url = create_flow_url(node_id=node_id, table_id=self.table_id, flow_id=str(self.flow_id))

        self.flow_id+=1
        self.group_id+=1

        r1 = requests.put(group_url, data=open('group.xml', 'rb'), auth=('admin', 'admin'), headers=self.header)
        print r1.text
        print r1.status_code
        print r1.content
        time.sleep(0.10)
        r2 = requests.put(flow_group_url, data=open('groupflow.xml', 'rb'), auth=('admin', 'admin'), headers=self.header)
        print r2.text
        print r2.status_code
        print r2.content


    def install_handle_failure_down_path(self, src, dst, node_reciever, node_sender, node_send_to):
        link1 = self.get_link(node_reciever, node_sender)
        in_port = link1[node_reciever]

        link2 = self.get_link(node_reciever, node_send_to)
        out_port = link2[node_reciever]

        print 'In install_handle_failure_down_path'
        print 'node_reciever:', node_reciever
        print 'node_sender:', node_sender
        print 'node_send_to:', node_send_to

        create_flow_with_inport(id_flow=str(self.flow_id), id_table=self.table_id, out_port=out_port, src_ip=src, dst_ip=dst, inport=in_port, priority=self.priority_down_link_break, filename='flow_inport_src_dst_match.xml')
        flow_url = create_flow_url(node_id=node_reciever, table_id=self.table_id, flow_id=str(self.flow_id))
        self.flow_id+=1

        r = requests.put(flow_url, data=open('flow_inport_src_dst_match.xml', 'rb'), auth=('admin', 'admin'), headers=self.header)
        print r.text

    def install_path(self, src, dst):

        paths = self.get_path(src, dst)

        # get host-node link and install flow
        # first node in both paths
        len_path1 = len(paths[0])
        len_path2 = len(paths[1])

        if (len_path1 > len_path2):
            tmp = paths[0]
            paths[0] = paths[1]
            paths[1] = tmp
            len_path1 = len(paths[0])
            len_path2 = len(paths[1])

        # istall this on the destination switch
        self.install_simple_flow(src=src, dst=dst, node_id=paths[0][len_path1 - 1])

        for path in paths:
            print path

        #create group and install flow at edge node (node connected to h1)
        self.install_group_and_flow(src=src, dst=dst, node_id=paths[0][0], node_to_connect1=paths[0][1],node_to_connect2=paths[1][1],return_flag=False)

        # add group and flow values on nodes on first path
        for i in range(1,len_path1-1):
            # node_to_connect2 needs to be changed to OFPP_IN_PORT = 4294967288, -1 used as a flag
            self.install_group_and_flow(src=src, dst=dst, node_id=paths[0][i], node_to_connect1=paths[0][i+1],node_to_connect2=paths[0][i-1], return_flag =True)

        for i in range(1, len_path2-1):
            self.install_group_and_flow(src=src, dst=dst, node_id=paths[1][i], node_to_connect1=paths[1][i+1],node_to_connect2=paths[1][i-1], return_flag=True)

        # rules added to handle returning traffic due to failure down the link.
        if (len_path1 > 2):
            for i in range(0, len_path1 - 2):
                # add higher priority rule to handle packets coming due to failure down the path
                # need to send packets in the opposite direction
                if (i == 0):
                    self.install_handle_failure_down_path(src=src, dst=dst, node_reciever=paths[0][i], node_sender=paths[0][i+1], node_send_to=paths[1][1])
                else:
                    self.install_handle_failure_down_path(src=src, dst=dst, node_reciever=paths[0][i], node_sender=paths[0][i+1], node_send_to=paths[0][i-1])

        if (len_path2 > 2):
            for i in range(0, len_path2 - 2):
                # add higher priority rule to handle packets coming due to failure down the path
                if (i==0):
                    self.install_handle_failure_down_path(src=src, dst=dst, node_reciever=paths[1][i], node_sender=paths[1][i+1], node_send_to=paths[0][1])
                else:
                    self.install_handle_failure_down_path(src=src, dst=dst, node_reciever=paths[1][i], node_sender=paths[1][i+1], node_send_to=paths[1][i-1])


def main():
    f = Flow_Synthesizer()

    f.install_path('10.0.0.1', '10.0.0.2')
    f.install_path('10.0.0.2', '10.0.0.1')

    print "Total flows installed:", (f.flow_id - 100)


if __name__ == "__main__":
    main()

