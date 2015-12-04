#!/usr/bin/env python3
# Copyright (c) 2015 Schweitzer Engineering Laboratories, Inc.

from __future__ import absolute_import
import sys
# import ConfigTree
from sel_controller import OperationalTree
from sel_controller import Session
import requests

def scan_and_adopt(tree, uri, id_headers, url_element, descriptor):
    for entry in tree.read_collection():
        if entry.state == OperationalTree.State.unadopted():
            url = u"{0}api/default/operational/{1}('{2}')/Sel.Adopt".format(
                uri,
                url_element,
                entry.id
            )

            resp = requests.post(url,
                                 data={},
                                 headers=id_headers)
            if not(200 <= resp.status_code and resp.status_code < 300):
                print resp.status_code
                print resp.text
            else:
                print u"Successfully adopted {0} {1}".format(descriptor, entry.id)
        else:
            print u"Skipped: {0} {1} in state {2}".format(descriptor.capitalize(),
                                                         entry.id,
                                                         entry.state)

def main(uri):

    session = Session.Http(uri)

    ## Uncomment for extra debug info
    #session.print_status = True
    #session.print_data = True

    session.auth_user_callback()
    id_headers = {u'Content-Type': u'application/json',
                  u'Authorization': u'Bearer ' + session.current_user_token}

    nodes_op_tree = OperationalTree.nodesHttpAccess(session)
    scan_and_adopt(nodes_op_tree, uri, id_headers, u'nodes', u'node')

    ports_op_tree = OperationalTree.portsHttpAccess(session)
    scan_and_adopt(ports_op_tree, uri, id_headers, u'ports', u'port')

    links_op_tree = OperationalTree.linksHttpAccess(session)
    scan_and_adopt(links_op_tree, uri, id_headers, u'links', u'link')


if __name__ == u'__main__':

    if len(sys.argv) != 2:
        print u'Give me the controller URI' + \
              u' (e.g. http://davibuehpc2.ad.selinc.com:1234/)'
    else:
        main(sys.argv[1])
