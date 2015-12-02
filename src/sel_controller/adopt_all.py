# Copyright (c) 2015 Schweitzer Engineering Laboratories, Inc.

from __future__ import absolute_import
import sys
# import ConfigTree
from sel_controller import OperationalTree
from sel_controller import Session
import requests

def main(uri):

    session = Session.Http(uri)

    ## Uncomment for extra debug info
    #session.print_status = True
    #session.print_data = True

    session.auth_user_callback()
    nodes_op_tree = OperationalTree.nodesHttpAccess(session)

    for node_entry in nodes_op_tree.read_collection():
        if node_entry.state == u"Unadopted":
            url = u"{0}api/default/operational/nodes('{1}')/Sel.Adopt".format(
                uri,
                node_entry.id
            )

            id_headers = {u'Content-Type': u'application/json',
                          u'Authorization': u'Bearer ' + session.current_user_token}
            resp = requests.post(url,
                                 data={},
                                 headers=id_headers)
            if not(200 <= resp.status_code and resp.status_code < 300):
                print resp.status_code
                print resp.text
            else:
                print u"Successfully adopted node {0}".format(node_entry.id)

if __name__ == u'__main__':

    if len(sys.argv) != 2:
        print u'Give me the controller URI' + \
              u' (e.g. http://davibuehpc2.ad.selinc.com:1234/)'
    else:
        main(sys.argv[1])
