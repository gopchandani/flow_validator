# Copyright (c) 2015 Schweitzer Engineering Laboratories, Inc.
import requests
import re
from oauth2client.client import OAuth2WebServerFlow
from requests.auth import HTTPBasicAuth

auth_code = ""

'''
from http://stackoverflow.com/questions/38987/how-can-i-merge-two-python-dictionaries-in-a-single-expression
Given any number of dicts, shallow copy and merge into a new dict,
precedence goes to key value pairs in latter dicts.
'''


def merge_dicts(*dict_args):
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


class Http(object):
    current_user_token = ""
    current_user_name = ""
    controller_base = ""
    api_base_url = None
    current_transaction_id = None
    print_status = False
    print_data = False

    json_application_type = {'Content-Type': 'application/json;odata.metadata=minimal', 'OData-Version': '4.0'}

    def __init__(self, base_url):
        self.controller_base = base_url
        self.api_base_url = base_url + "api/"
      
    def auth_user_callback(self, user="hobbs", role="Engineer", password="Asdf123$"):
        post_resp = requests.post(self.controller_base + "identity/connect/token",
                                  auth=HTTPBasicAuth('uiuc-validator-client', 'supersecret'),
                                  data = { "grant_type": "password", 
                                    "scope": "Rest", 
                                    "username":user, 
                                    "password":password, 
                                    "acr_values": "role:"+role }
                          , headers = {'Content-Type': 'application/x-www-form-urlencoded'})
        self.current_user_name = user
        self.current_user_token = post_resp.json()["access_token"]
        return self.current_user_token


    def create_authorization_header(self):
        bearer_token = 'Bearer ' + self.current_user_token
        return {'authorization': bearer_token}

    def get_data(self, url_extension):
        parameters = None if self.current_transaction_id is None else {"transactionId", self.current_transaction_id}
        url = self.api_base_url + url_extension
        result = None
        try:
            result = requests.get(url, data=None,
                                  headers=merge_dicts(self.json_application_type, self.create_authorization_header()),
                                  params=parameters)
        except Exception as e:
            print(('Unable to GET from URL: ' + url))
            print(('Reason ' + e))
        content = result.text
        self._print_status("GET", url, result.status_code)
        self._print_data(content)
        return content

    def post_data(self, url_extension, raw_data):
        parameters = None if self.current_transaction_id is None else {"transactionId", self.current_transaction_id}
        url = self.api_base_url + url_extension
        result = None
        try:
            result = requests.post(url, data=raw_data,
                                   headers=merge_dicts(self.json_application_type, self.create_authorization_header()),
                                   params=parameters)
        except Exception as e:
            print(('Unable to POST to URL: ' + url))
            print(('Reason ' + e))
        content = result.text
        self._print_status("GET", url, result.status_code)
        self._print_data(content)
        return content

    def put_data(self, url_extension, raw_data):
        parameters = None if self.current_transaction_id is None else {"transactionId", self.current_transaction_id}
        url = self.api_base_url + url_extension
        result = None
        try:
            result = requests.post(url, data=raw_data,
                                   headers=merge_dicts(self.json_application_type, self.create_authorization_header()),
                                   params=parameters)
        except Exception as e:
            print(('Unable to PUT to URL: ' + url))
            print(('Reason ' + e))
        self.print_status("PUT", url, result.status_code)
        return result

    def patch_data(self, url_extension, raw_data):
        parameters = None if self.current_transaction_id is None else {"transactionId", self.current_transaction_id}
        url = self.api_base_url + url_extension
        result = None
        try:
            result = requests.patch(url, data=raw_data,
                                    headers=merge_dicts(self.json_application_type, self.create_authorization_header()),
                                    params=parameters)
        except Exception as e:
            print(('Unable to PATCH to URL: ' + url))
            print(('Reason ' + e))
        self.print_status("PATCH", url, result.status_code)
        return result

    def delete_data(self, url_extension):
        parameters = None if self.current_transaction_id is None else {"transactionId", self.current_transaction_id}
        url = self.api_base_url + url_extension
        result = None
        try:
            result = requests.delete(url,
                                     headers=merge_dicts(self.json_application_type, self.create_authorization_header()),
                                     params=parameters)
        except Exception as e:
            print(('Unable to DELETE data at URL: ' + url))
            print(('Reason ' + e))
        self.print_status("DELETE", url, result.status_code)
        return result

    def _print_status(self, operation, url, status):
        if self.print_status:
            print(('{0} URL: {1}'.format(operation, url)))
            print(('Status Code:' + str(status)))

    def _print_data(self, data):
        if self.print_data:
            print(('{:-^30}'.format('Begin Content')))
            print(data)
            print(('{:-^30}'.format('End Content')))
