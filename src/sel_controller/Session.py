# Copyright (c) 2015 Schweitzer Engineering Laboratories, Inc.

from __future__ import absolute_import
import requests
from requests.auth import HTTPBasicAuth
import json
u'''
from http://stackoverflow.com/questions/38987/how-can-i-merge-two-python-dictionaries-in-a-single-expression
Given any number of dicts, shallow copy and merge into a new dict,
precedence goes to key value pairs in latter dicts.
'''


#from __future__ import absolute_import
def merge_dicts(*dict_args):
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


class Http(object):
    current_user_token = u""
    current_user_name = u""
    controller_base = u""
    api_base_url = None
    current_transaction_id = None
    print_status = False
    print_data = False

    json_application_type = {u'Content-Type': u'application/json;odata.metadata=minimal', u'OData-Version': u'4.0'}

    def __init__(self, base_url):
        self.controller_base = base_url
        self.api_base_url = base_url + u"api/"

    def auth_user_callback(self, user, role, password):
        post_resp = requests.post(self.controller_base + u"identity/connect/token",
                                  auth=HTTPBasicAuth(u'password-client', u'8b2cacd9d07219d0af89cf1c2280d071'),
                                  data = { u"grant_type": u"password",
                                    u"scope": u"Rest",
                                    u"username":user,
                                    u"password":password,
                                    u"acr_values": u"role:"+role}
                          , headers = {u'Content-Type': u'application/x-www-form-urlencoded'})
        self.current_user_name = user
        self.current_user_token = post_resp.json()[u"access_token"]
        return self.current_user_token


    def create_authorization_header(self):
        bearer_token = u'Bearer ' + self.current_user_token
        return {u'authorization': bearer_token}

    def get_data(self, url_extension):
        parameters = None if self.current_transaction_id is None else set([u"transactionId", self.current_transaction_id])
        url = self.api_base_url + url_extension
        result = None
        try:
            result = requests.get(url, data=None,
                                  headers=merge_dicts(self.json_application_type, self.create_authorization_header()),
                                  params=parameters)
        except Exception, e:
            print u'Unable to GET from URL: ' + url
            print u'Reason ' + e
        content = result.text
        self._print_status(u"GET", url, result.status_code)
        self._print_data(content)
        return content

    def post_data(self, url_extension, raw_data):
        parameters = None if self.current_transaction_id is None else set([u"transactionId", self.current_transaction_id])
        url = self.api_base_url + url_extension
        result = None
        try:
            result = requests.post(url, data=raw_data,
                                   headers=merge_dicts(self.json_application_type, self.create_authorization_header()),
                                   params=parameters)
        except Exception, e:
            print u'Unable to POST to URL: ' + url
            print u'Reason ' + e
        content = result.text
        self._print_status(u"POST", url, result.status_code)
        self._print_data(content)
        return content

    def put_data(self, url_extension, raw_data):
        parameters = None if self.current_transaction_id is None else set([u"transactionId", self.current_transaction_id])
        url = self.api_base_url + url_extension
        result = None
        try:
            result = requests.put(url, data=raw_data,
                                   headers=merge_dicts(self.json_application_type, self.create_authorization_header()),
                                   params=parameters)
        except Exception, e:
            print u'Unable to PUT to URL: ' + url
            print u'Reason ' + e
        self._print_status(u"PUT", url, result.status_code)
        return result

    def patch_data(self, url_extension, raw_data):
        parameters = None if self.current_transaction_id is None else set([u"transactionId", self.current_transaction_id])
        url = self.api_base_url + url_extension
        result = None
        try:
            result = requests.patch(url, data=raw_data,
                                    headers=merge_dicts(self.json_application_type, self.create_authorization_header()),
                                    params=parameters)
        except Exception, e:
            print u'Unable to PATCH to URL: ' + url
            print u'Reason ' + unicode(e)
        self._print_status(u"PATCH", url, result.status_code)
        return result

    def delete_data(self, url_extension):
        parameters = None if self.current_transaction_id is None else set([u"transactionId", self.current_transaction_id])
        url = self.api_base_url + url_extension
        result = None
        try:
            result = requests.delete(url,
                                     headers=merge_dicts(self.json_application_type, self.create_authorization_header()),
                                     params=parameters)
        except Exception, e:
            print u'Unable to DELETE data at URL: ' + url
            print u'Reason ' + unicode(e)
        self._print_status(u"DELETE", url, result.status_code)
        return result

    def _print_status(self, operation, url, status):
        if self.print_status:
            print u'{0} URL: {1}'.format(operation, url)
            print u'Status Code:' + unicode(status)

    def _print_data(self, data):
        if self.print_data:
            print u'{:-^30}'.format(u'Begin Content')
            print data
            print u'{:-^30}'.format(u'End Content')


def connect_session(controller_uri=u'http://localhost:1234/', username=u'', password=u'', role=u'Readonly'):
    session = HttpSession(controller_uri)
    session.auth_user_callback( username, role, password)
    return session


class EntityAccess(object):
    def __init__(self, session, api_path, resolver):
        self.resolver = resolver
        self._session = session
        self.api_tree_path = api_path
        self.entity_base_name = u""
        self.entity_odata_type = u""

    def read_single(self, item_id):
        entity_path = self.api_tree_path + self.entity_base_name + u"('" + item_id + u"')"
        response = self._session.get_data(entity_path)
        if len(response) == 0:
            return None
        pyson_response = json.loads(response)
        object_type = pyson_response[u'@odata.type'] if u'@odata.type' in pyson_response else self.entity_odata_type
        result = self.resolver.get_new_object(object_type)
        result.from_pyson(pyson_response)
        return result

    def read_collection(self):
        collection_path = self.api_tree_path + self.entity_base_name
        response = self._session.get_data(collection_path)
        if len(response) == 0:
            return None
        pyson_response = json.loads(response)
        result = []
        #raw_json_list = pyson_response[u'value']
        raw_json_list = pyson_response[u'value']
        for pyson_object in raw_json_list:
            object_type = pyson_object[u'@odata.type'] if u'@odata.type' in pyson_object else self.entity_odata_type
            new_object = self.resolver.get_new_object(object_type)
            new_object.from_pyson(pyson_object)
            result.append(new_object)
        return result

    def create_single(self, item):
        json_string = item.to_json()
        collection_path = self.api_tree_path + self.entity_base_name
        response = self._session.post_data(collection_path, json_string)
        if len(response) == 0:
            return None
        pyson_response = json.loads(response)
        object_type = pyson_response[u'@odata.type'] if u'@odata.type' in pyson_response else self.entity_odata_type
        result = self.resolver.get_new_object(object_type)
        result.from_pyson(pyson_response)
        return result

    def execute_action(self, item_id, pyson, action_namespace, action_name):
        json_string = json.dumps(pyson)
        collection_path = self.api_tree_path + self.entity_base_name + u"('" + item_id + u"')" + \
            action_namespace + u'.' + action_name + u'()'
        response = self._session.post_data(collection_path, json_string)
        if len(response) == 0:
            return None
        pyson_response = json.loads(response)
        return pyson_response

    def update_single(self, item, item_id):
        item_json = item.to_json()
        entity_path = self.api_tree_path + self.entity_base_name + u"('" + item_id + u"')"
        response = self._session.put_json_data(entity_path, item_json)
        return response

    def patch_single(self, item, item_id, update_key_list):
        item_pyson = item.to_pyson()
        patch = {}
        for key in update_key_list:
            patch[key] = item_pyson[key]
        entity_path = self.api_tree_path + self.entity_base_name + u"('" + item_id + u"')"
        json_string = json.dumps(patch, sort_keys=True, indent=4, separators=(u',', u': '))
        response = self._session.patch_json_data(entity_path, json_string)
        return response

    def delete_single(self, item_id):
        entity_path = self.api_tree_path + self.entity_base_name + u"('" + item_id + u"')"
        response = self._session.delete_data(entity_path)
        return response
