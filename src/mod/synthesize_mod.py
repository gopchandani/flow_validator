__author__ = 'Rakesh Kumar'

from model.model import Model
from synthesis.create_url import create_group_url, create_flow_url

import httplib2
import json



class SynthesizeMod():

    def __init__(self):
        self.model = Model()

    def _create_mpls_tag_apply_rule(self, flow_id, table_id, out_port):

        flow = dict()

        flow["flags"] = ""
        flow["table_id"] = table_id
        flow["id"] = str(flow_id)
        flow["priority"] = 1
        flow["idle-timeout"] = 0
        flow["hard-timeout"] = 0
        flow["cookie"] = flow_id
        flow["cookie_mask"] = 255

        #Compile match
        ethernet_type = {"type": str(0x0800)}
        ethernet_match = {"ethernet-type": ethernet_type}
        match = {"ethernet-match": ethernet_match}
        flow["match"] = match

        #Compile action
        output_action = {"output-node-connector": out_port}
        action = {"output-actions": output_action}
        apply_actions = {"action": action, "order": 0}
        instruction = {"apply-actions":apply_actions, "order": 0}
        instructions = {"instruction":instruction}
        flow["instructions"] = instructions

        return flow

    def _populate_switch(self, node_id):


        #port_list = self.model.graph.node[n]["port_list"]
        #print port_list

        table_id = 0
        flow_id = 1
        out_port = 1

        flow = self._create_mpls_tag_apply_rule(flow_id, table_id, out_port)
        url = url = create_flow_url(node_id, table_id, str(flow_id))

        print flow
        print url
        print json.dumps(flow)

        h = httplib2.Http(".cache")
        h.add_credentials('admin', 'admin')
        resp, content = h.request(url, "PUT",
                                  headers={'Content-Type': 'application/json; charset=UTF-8'},
                                  body=json.dumps(flow))

        print resp, content

        #r = requests.put(url, data=open('simple.xml', 'rb'), auth=('admin', 'admin'), headers=self.header)


    def trigger(self):

        #  First figure out what switches exist in the current topology
        #  Each switch needs the same thing (logically) inside it

        for n in self.model.graph.nodes():

            if self.model.graph.node[n]["node_type"] == "switch":
                print "We are in business here at n:", self.model.graph.node[n]["node_type"], n
                self._populate_switch(n)



def main():
    sm = SynthesizeMod()

    sm.trigger()

if __name__ == "__main__":
    main()

