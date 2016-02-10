# Copyright (c) 2015 Schweitzer Engineering Laboratories, Inc.
from __future__ import absolute_import
import json


class HttpAccess(object):
    def __init__(self, session, api_path, resolver):
        self.resolver = resolver
        self._session = session
        self.api_tree_path = api_path
        self.entity_base_name = u""
        self.entity_odata_type = u""

    def read_single(self, item_id):
        entity_path = self.api_tree_path + self.entity_base_name + u"('" + item_id + u"')"
        response = self._session.get_data(entity_path)
        pyson_response = json.loads(response)
        object_type = pyson_response[u'@odata.type'] if u'@odata.type' in pyson_response else self.entity_odata_type
        result = self.resolver.get_new_object(object_type)
        result.from_pyson(pyson_response)
        return result

    def read_collection(self):
        collection_path = self.api_tree_path + self.entity_base_name
        response = self._session.get_data(collection_path)
        pyson_response = json.loads(response)
        result = []
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
        response = self._session.delete_json_data(entity_path)
        return response
