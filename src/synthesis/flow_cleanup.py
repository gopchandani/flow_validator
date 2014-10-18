__author__ = 'Rakesh Kumar'


import json
import sys
import pprint
import httplib2
import urllib

class Flow_Cleanup:

    def __init__(self):
        baseUrl = 'http://localhost:8181/restconf/'
        h = httplib2.Http(".cache")
        h.add_credentials('admin', 'admin')

        # Get all the nodes/switches from the inventory API
        remaining_url = 'operational/opendaylight-inventory:nodes'
        resp, content = h.request(baseUrl + remaining_url, "GET")
        nodes = json.loads(content)

        for node in nodes["nodes"]["node"]:

            node_id = node["id"]
            switch_flow_tables = []

            for flow_table in node["flow-node-inventory:table"]:

                flow_table_id = flow_table["id"]

                #print "flow_table_id:", flow_table

                if "flow" not in flow_table:
                    continue

                for flow in flow_table["flow"]:
                    print flow

                    if "id" in flow:
                        flow_id = flow["id"]
                        print "flow_id:", flow_id

                        print "Operational:"

                        remaining_url = "operational/opendaylight-inventory:nodes/node/" + str(node_id) + \
                                        "/flow-node-inventory:table/" + str(flow_table_id) +"/" + "flow" + "/" + \
                                        urllib.quote(str(flow_id).encode("utf8")) + "/"

                        resp, content = h.request(baseUrl + remaining_url, "GET")
                        print resp["status"], resp, content

                        print "Config"

               #         remaining_url = "config/opendaylight-inventory:nodes/node/" + str(node_id) + \
               #                         "/flow-node-inventory:table/" + str(flow_table_id) +"/" + \
               #                         "flow" + "/" + \
               #                         urllib.quote(str(flow_id).encode("utf8")) + "/"

                        remaining_url = "config/opendaylight-inventory:nodes/node/" + str(node_id)# + \
                                        #"/flow-node-inventory:table/" + str(flow_table_id) +"/" + \
                                        #"flow" + "/" + \
                                        #urllib.quote(str(flow_id).encode("utf8")) + "/"

                        resp, content = h.request(baseUrl + remaining_url, "GET")
                        print resp["status"], resp, content

def main():
    f = Flow_Cleanup()

if __name__ == "__main__":
    main()

