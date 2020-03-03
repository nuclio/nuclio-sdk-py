# Copyright 2017 The Nuclio Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import nuclio_sdk
import nuclio_sdk.helpers

# different HTTP client libraries for Python 2/3
if nuclio_sdk.helpers.PYTHON2:
    from httplib import HTTPConnection
else:
    from http.client import HTTPConnection


class Platform(object):

    def __init__(self, kind, namespace='default', connection_provider=None):
        self.kind = kind
        self.namespace = namespace

        # connection_provider is used for unit testing
        self._connection_provider = connection_provider or HTTPConnection

    def call_function(self, function_name, event, node=None, timeout=None):

        # prepare the request headers / body
        request_headers, request_body = self._prepare_request(function_name, event)

        # delegate the request to callee function
        response_headers, response_body, response_status_code = self._call_function(function_name,
                                                                                    event,
                                                                                    request_body,
                                                                                    request_headers,
                                                                                    timeout)

        # return callee response to client
        return nuclio_sdk.Response(headers=response_headers,
                                   body=response_body,
                                   content_type=response_headers.get('content-type', 'text/plain'),
                                   status_code=response_status_code)

    def _prepare_request(self, function_name, event):

        # if the user passes a dict as a body, assume json serialization. otherwise take content type from
        # body or use plain text
        if isinstance(event.body, dict):
            body = nuclio_sdk.json.dumps(event.body)
            content_type = 'application/json'
        else:
            body = event.body
            content_type = event.content_type or 'text/plain'

        # use the headers from the event or default to empty dict
        headers = event.headers or {}
        headers['Content-Type'] = content_type

        # if no override header, use the name of the function to indicate the target
        # this is needed to cold start a function in case it was scaled to zero
        headers['X-Nuclio-Target'] = event.headers.get('X-Nuclio-Target', function_name)
        return headers, body

    def _call_function(self, function_name, event, body, headers, timeout):

        # get connection from provider
        connection = self._connection_provider(self._get_function_url(function_name), timeout=timeout)

        try:
            connection.request(event.method, event.path, body=body, headers=headers)

            # get response from connection
            response = connection.getresponse()

            # get response headers as lowercase
            headers = {
                name.lower(): value
                for (name, value) in response.getheaders()
            }

            # read the body
            body = response.read()

            # if content type is json, go ahead and do parsing here. if it explodes, don't blow up
            if headers.get('content-type') == 'application/json':
                body = self._try_parse_json(body)

            return headers, body, response.status

        finally:
            connection.close()

    def _try_parse_json(self, data):
        try:
            return nuclio_sdk.json.loads(data)
        except:
            return data

    def _get_function_url(self, function_name):

        # local envs prefix namespace
        if self.kind == 'local':
            return '{0}-{1}:8080'.format(self.namespace, function_name)
        else:
            return '{0}:8080'.format(function_name)
