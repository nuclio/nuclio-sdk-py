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

import json
import http.client

import nuclio_sdk
import nuclio_sdk.helpers


class Platform(object):
    def __init__(
        self,
        kind,
        namespace="default",
        connection_provider=None,
        on_control_callback=None,
    ):
        self.kind = kind
        self.namespace = namespace

        # connection_provider is used for unit testing
        self._connection_provider = connection_provider or http.client.HTTPConnection

        self._control_callback = on_control_callback
        self._termination_callback = None
        self._drain_callback = None

    async def explicit_ack(self, qualified_offset):
        """
        Notifying the processor to ack on a qualified offset

        :param qualified_offset: the qualified offset to ack
        :type qualified_offset: QualifiedOffset
        """
        message = qualified_offset.compile_explicit_ack_message()
        if self._control_callback:
            await self._control_callback(message)
        else:
            raise Exception(
                "Cannot send explicit ack since control callback was not initialized"
            )

    def set_drain_callback(self, callback):
        """
        Register a callback to be called when the platform is draining (rebalance happening in stream).
        If already registered, the callback will be replaced.
        When called, the callback will be called with zero arguments.

        :param callback: the callback to call when terminating
        """
        self._drain_callback = callback

    def set_termination_callback(self, callback):
        """
        Register a callback to be called when the platform is terminating.
        If already registered, the callback will be replaced.
        When called, the callback will be called with zero arguments.

        :param callback: the callback to call when terminating
        """
        self._termination_callback = callback

    def call_function(
        self, function_name, event, node=None, timeout=None, service_name_override=None
    ):
        # get connection from provider
        connection = self._connection_provider(
            self._get_function_url(function_name, service_name_override),
            timeout=timeout,
        )

        # if the user passes a dict as a body, assume json serialization. otherwise take content type from
        # body or use plain text
        if isinstance(event.body, dict):
            body = json.dumps(event.body)
            content_type = "application/json"
        else:
            body = event.body
            content_type = event.content_type or "text/plain"

        # use the headers from the event or default to empty dict
        headers = event.headers or {}
        headers["Content-Type"] = content_type

        # if no override header, use the name of the function to indicate the target
        # this is needed to cold start a function in case it was scaled to zero
        headers["X-Nuclio-Target"] = event.headers.get("X-Nuclio-Target", function_name)

        # let http client determine that
        headers.pop("Content-Length", None)

        try:
            connection.request(event.method, event.path, body=body, headers=headers)

            # get response from connection
            response = connection.getresponse()

            # read the body
            response_body = response.read()
        finally:
            connection.close()

        # header dict
        response_headers = {}

        # get response headers as lowercase
        for name, value in response.getheaders():
            response_headers[name.lower()] = value

        # if content type exists, use it
        response_content_type = response_headers.get("content-type", "text/plain")

        # if content type is json, go ahead and do parsing here. if it explodes, don't blow up
        if response_content_type == "application/json":
            response_body = json.loads(response_body)

        return nuclio_sdk.Response(
            headers=response_headers,
            body=response_body,
            content_type=response_content_type,
            status_code=response.status,
        )

    def _get_function_url(self, function_name, service_name_override=None):
        # local envs prefix namespace
        if self.kind == "local":
            service_name = service_name_override or "nuclio-{0}-{1}".format(
                self.namespace, function_name
            )
        else:
            service_name = service_name_override or "nuclio-{0}".format(function_name)
        return "{0}:8080".format(service_name)

    def _on_signal(self, callback_type="termination"):
        """
        When a signal is received, call the termination/drain callback as a hook before exiting
        If not set, the callback will be a no-op

        :arg callback_type:str - callback type, can be "termination" or "drain"
        """
        if callback_type == "termination" and self._termination_callback:
            return self._termination_callback()
        elif callback_type == "drain" and self._drain_callback:
            return self._drain_callback()
