__author__ = 'Rakesh Kumar'


import json
import sys
import pprint
import httplib2

class Flow_Cleanup:

    def __init__(self):
        baseUrl = 'http://localhost:8181/restconf/'
        h = httplib2.Http(".cache")
        h.add_credentials('admin', 'admin')

        # Get all the nodes/switches from the inventory API
        remaining_url = 'config/opendaylight-inventory:nodes'
        resp, content = h.request(baseUrl + remaining_url, "GET")
        nodes = json.loads(content)


        for node in nodes["nodes"]["node"]:

            node_id = node["id"]
            switch_flow_tables = []

            for flow_table in node["flow-node-inventory:table"]:
                print(flow_table)
                flow_table_id = flow_table["id"]

                remaining_url = "config/opendaylight-inventory:nodes/node/" + str(node_id) + \
                                "/flow-node-inventory:table/" + str(flow_table_id) +"/"

                resp, content = h.request(baseUrl + remaining_url, "DELETE")

                print resp, content
                #table = json.loads(content)
                #pprint(table)




def main():
    f = Flow_Cleanup()

if __name__ == "__main__":
    main()

