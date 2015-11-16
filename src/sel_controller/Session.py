# Copyright (c) 2015 Schweitzer Engineering Laboratories, Inc.
import requests
import re
from oauth2client.client import OAuth2WebServerFlow
from requests.auth import HTTPBasicAuth

auth_code = u""

u'''
from http://stackoverflow.com/questions/38987/how-can-i-merge-two-python-dictionaries-in-a-single-expression
Given any number of dicts, shallow copy and merge into a new dict,
precedence goes to key value pairs in latter dicts.
'''


from __future__ import absolute_import
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
      
    def auth_user_callback(self, user=u"hobbs", role=u"Engineer", password=u"Asdf123$"):
        post_resp = requests.post(self.controller_base + u"identity/connect/token",
                                  auth=HTTPBasicAuth(u'uiuc-validator-client', u'supersecret'),
                                  data = { u"grant_type": u"password", 
                                    u"scope": u"Rest", 
                                    u"username":user, 
                                    u"password":password, 
                                    u"acr_values": u"role:"+role }
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
            print (u'Unable to GET from URL: ' + url)
            print (u'Reason ' + e)
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
            print (u'Unable to POST to URL: ' + url)
            print (u'Reason ' + e)
        content = result.text
        self._print_status(u"GET", url, result.status_code)
        self._print_data(content)
        return content

    def put_data(self, url_extension, raw_data):
        parameters = None if self.current_transaction_id is None else set([u"transactionId", self.current_transaction_id])
        url = self.api_base_url + url_extension
        result = None
        try:
            result = requests.post(url, data=raw_data,
                                   headers=merge_dicts(self.json_application_type, self.create_authorization_header()),
                                   params=parameters)
        except Exception, e:
            print (u'Unable to PUT to URL: ' + url)
            print (u'Reason ' + e)
        self.print_status(u"PUT", url, result.status_code)
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
            print (u'Unable to PATCH to URL: ' + url)
            print (u'Reason ' + e)
        self.print_status(u"PATCH", url, result.status_code)
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
            print (u'Unable to DELETE data at URL: ' + url)
            print (u'Reason ' + e)
        self.print_status(u"DELETE", url, result.status_code)
        return result

    def _print_status(self, operation, url, status):
        if self.print_status:
            print (u'{0} URL: {1}'.format(operation, url))
            print (u'Status Code:' + unicode(status))

    def _print_data(self, data):
        if self.print_data:
            print (u'{:-^30}'.format(u'Begin Content'))
            print data
            print (u'{:-^30}'.format(u'End Content'))
