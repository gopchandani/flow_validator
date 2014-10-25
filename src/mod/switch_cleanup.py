__author__ = 'Rakesh Kumar'


import json
import sys
import pprint
import httplib2
import urllib

class SwitchCleanup:

    def cleanup_flow_table(self, node_id, flow_table):

        flow_table_id = flow_table["id"]

        if "flow" not in flow_table:
            return

        print "flow_table_id:", flow_table["id"], "len(flow_table['flow''])", len(flow_table["flow"])

        for flow in flow_table["flow"]:

            if "id" in flow:
                flow_id = flow["id"]
                print "flow_id:", flow_id

                print "Operational:"

                remaining_url = "operational/opendaylight-inventory:nodes/node/" + str(node_id) + \
                                "/flow-node-inventory:table/" + str(flow_table_id) +"/" + "flow" + "/" + \
                                urllib.quote(str(flow_id).encode("utf8")) + "/"

                resp, content = self.h.request(self.baseUrl + remaining_url, "GET")
                print resp["status"], resp, content
                print content

                flow_rule = json.loads(content)["flow-node-inventory:flow"][0]
                for key in flow_rule:
                    print key, ":", flow_rule[key]

                # print "Config"
                #
                # remaining_url = "config/opendaylight-inventory:nodes/node/" + str(node_id) + \
                #                 "/flow-node-inventory:table/" + str(flow_table_id) +"/" + \
                #                 "flow" + "/" + \
                #                 urllib.quote(str(flow_id).encode("utf8")) + "/"
                #
                # print baseUrl+remaining_url
                #
                # resp, content = h.request(baseUrl + remaining_url, "GET")
                # print resp["status"], resp, content
                #
                # resp, content = h.request(baseUrl + remaining_url, "GET")
                # print resp["status"], resp, content

    def cleanup_group_table(self, node_id, group_table):
        pprint.pprint(group_table)

    def __init__(self):
        self.baseUrl = 'http://localhost:8181/restconf/'
        self.h = httplib2.Http(".cache")
        self.h.add_credentials('admin', 'admin')

        # Get all the nodes/switches from the inventory API
        remaining_url = 'config/opendaylight-inventory:nodes'
        resp, content = self.h.request(self.baseUrl + remaining_url, "GET")
        nodes = json.loads(content)

        for node in nodes["nodes"]["node"]:

            node_id = node["id"]
            switch_flow_tables = []

            # Flow Tables
            #for flow_table in node["flow-node-inventory:table"]:
            #    self.cleanup_flow_table(node_id, flow_table)

            #  Groups

            if "flow-node-inventory:group" in node:
                self.cleanup_group_table(node_id, node["flow-node-inventory:group"])


def main():
    f = SwitchCleanup()

if __name__ == "__main__":
    main()

