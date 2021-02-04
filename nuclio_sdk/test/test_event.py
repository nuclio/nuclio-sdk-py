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

import sys
import json

import nuclio_sdk.test
import nuclio_sdk.helpers
import nuclio_sdk.json_encoder


class TestEvent(nuclio_sdk.test.TestCase):
    def setUp(self):
        self._runtime_version = f"{sys.version_info.major}.{sys.version_info.minor}"

    def test_event_to_json_bytes_body(self):
        event = nuclio_sdk.Event(
            body=b"bytes-body",
            content_type="content-type",
            trigger=nuclio_sdk.TriggerInfo(kind="http", name="my-http-trigger"),
            method="GET",
        )
        event_json = event.to_json()
        serialized_event = nuclio_sdk.json_encoder.json.loads(event_json)
        self.assertEqual(serialized_event["body"], "Ynl0ZXMtYm9keQ==")
        self.assertEqual(serialized_event["content_type"], "content-type")
        self.assertEqual(serialized_event["method"], "GET")
        self.assertEqual(
            serialized_event["trigger"], {"kind": "http", "name": "my-http-trigger"}
        )
        self.assertEqual(serialized_event["last_in_batch"], False)
        self.assertEqual(serialized_event["offset"], 0)

    def test_event_to_json_bytes_non_utf8able_body(self):
        event = nuclio_sdk.Event(body=b"\x80abc")
        event_json = event.to_json()
        serialized_event = nuclio_sdk.json_encoder.json.loads(event_json)
        self.assertEqual(serialized_event["body"], "gGFiYw==")

    def test_event_to_json_string_body(self):
        request_body = "str-body"
        event = nuclio_sdk.Event(body=request_body)
        jsonized_event = nuclio_sdk.json_encoder.json.loads(event.to_json())
        self.assertEqual(request_body, jsonized_event["body"])

    def test_msgpack_serializer(self):
        event = nuclio_sdk.Event(
            body="some-body",
            content_type="content-type",
            trigger=nuclio_sdk.TriggerInfo(kind="http", name="my-http-trigger"),
            method="GET",
        )

        event_json = {k: v for k, v in json.loads(event.to_json()).items()}

        # encode dict keys for python > 3.6 (as nuclio uses msgpack with runtime > 3.6)
        if self._runtime_version != "3.6":
            self._event_keys_to_byte_string(event_json)

        msgpack_event_serializer = nuclio_sdk.EventSerializerFactory.create(
            "msgpack", runtime_version=self._runtime_version
        )
        serialized_event = msgpack_event_serializer.serialize(event_json)
        self.assertEqual(event.body, serialized_event.body)
        self.assertEqual(event.trigger.kind, serialized_event.trigger.kind)

    def _event_keys_to_byte_string(self, d):
        for k, v in list(d.items()):
            if isinstance(k, str):
                d[k.encode()] = v
                del d[k]
            if isinstance(v, dict):
                self._event_keys_to_byte_string(v)
