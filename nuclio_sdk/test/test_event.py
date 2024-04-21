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
import datetime
import json

import nuclio_sdk.test
import nuclio_sdk.helpers
import nuclio_sdk.json_encoder


class TestEvent:
    def test_event_to_json_bytes_body(self):
        event = nuclio_sdk.Event(
            body=b"bytes-body",
            content_type="content-type",
            trigger=nuclio_sdk.TriggerInfo(kind="http", name="my-http-trigger"),
            method="GET",
        )
        serialized_event = self._deserialize_event(event)
        self.assertEqual(serialized_event.body, "Ynl0ZXMtYm9keQ==")
        self.assertEqual(serialized_event.content_type, "content-type")
        self.assertEqual(serialized_event.method, "GET")
        self.assertDictEqual(
            serialized_event.trigger.__dict__,
            {"kind": "http", "name": "my-http-trigger"},
        )
        self.assertFalse(serialized_event.last_in_batch)
        self.assertEqual(serialized_event.offset, 0)

    def test_batch_to_json_bytes_body(self):
        trigger_name = "my-http-trigger"
        trigger_kind = "http"
        event_batch = [
            nuclio_sdk.Event(
                body=b"bytes-body-1",
                content_type="content-type",
                trigger=nuclio_sdk.TriggerInfo(kind=trigger_kind, name=trigger_name),
                method="GET",
            ),
            nuclio_sdk.Event(
                body=b"bytes-body-2",
                content_type="content-type",
                trigger=nuclio_sdk.TriggerInfo(kind=trigger_kind, name=trigger_name),
                method="GET",
            ),
        ]
        serialized_event_batch = self._deserialize_event(event_batch)
        item1 = serialized_event_batch[0]
        item2 = serialized_event_batch[1]
        self.assertEqual(item1.body, "Ynl0ZXMtYm9keS0x")
        self.assertEqual(item2.body, "Ynl0ZXMtYm9keS0y")
        for item in [item1, item2]:
            self.assertEqual(item.content_type, "content-type")
            self.assertEqual(item.method, "GET")
            self.assertDictEqual(
                item.trigger.__dict__,
                {"kind": trigger_kind, "name": trigger_name},
            )
            self.assertFalse(item.last_in_batch)
            self.assertEqual(item.offset, 0)

    def test_event_to_json_bytes_non_utf8able_body(self):
        event = nuclio_sdk.Event(body=b"\x80abc")
        serialized_event = self._deserialize_event(event)
        self.assertEqual(serialized_event.body, "gGFiYw==")

    def test_batch_to_json_bytes_non_utf8able_body(self):
        event_batch = [
            nuclio_sdk.Event(body=b"\x80abc"),
            nuclio_sdk.Event(body=b"\x80abcd"),
        ]
        serialized_event_batch = self._deserialize_event(event_batch)
        self.assertEqual(serialized_event_batch[0].body, "gGFiYw==")
        self.assertEqual(serialized_event_batch[1].body, "gGFiY2Q=")

    def test_event_to_json_string_body(self):
        request_body = "str-body"
        topic = "my-topic"
        event = nuclio_sdk.Event(body=request_body, topic=topic)
        serialized_event = self._deserialize_event(event)
        self.assertEqual(request_body, serialized_event.body)
        self.assertEqual(topic, serialized_event.topic)

    def test_print_event(self):
        """
        Test that printing an event doesn't raise an exception
        """
        event = nuclio_sdk.Event(body=datetime.datetime(2022, 1, 1))
        print(event)

    def _deserialize_event(self, event):
        raise NotImplementedError


class TestEventMsgPack(nuclio_sdk.test.TestCase, TestEvent):
    def _deserialize_event(self, event):
        if isinstance(event, list):
            event_json = [
                {k: v for k, v in json.loads(item.to_json()).items()} for item in event
            ]
        else:
            event_json = {k: v for k, v in json.loads(event.to_json()).items()}
        return nuclio_sdk.event.Event.deserialize(
            event_json, nuclio_sdk.event.EventDeserializerKinds.msgpack
        )


class TestEventMsgPackRaw(nuclio_sdk.test.TestCase, TestEvent):
    def _deserialize_event(self, event):
        if isinstance(event, list):
            event_json = [
                {k: v for k, v in json.loads(item.to_json()).items()} for item in event
            ]
            for item in event_json:
                self._event_keys_to_byte_string(item)
        else:
            event_json = {k: v for k, v in json.loads(event.to_json()).items()}
            self._event_keys_to_byte_string(event_json)
        return nuclio_sdk.event.Event.deserialize(
            event_json, nuclio_sdk.event.EventDeserializerKinds.msgpack_raw
        )

    def _event_keys_to_byte_string(self, d):
        for k, v in list(d.items()):
            if isinstance(k, str):
                d[k.encode()] = v
                del d[k]
            if isinstance(v, dict):
                self._event_keys_to_byte_string(v)


class TestEventJson(nuclio_sdk.test.TestCase, TestEvent):
    def _deserialize_event(self, event):
        if isinstance(event, list):
            event_json = [
                {k: v for k, v in json.loads(item.to_json()).items()} for item in event
            ]
        else:
            event_json = {k: v for k, v in json.loads(event.to_json()).items()}
        return nuclio_sdk.event.Event.deserialize(
            json.dumps(event_json), nuclio_sdk.event.EventDeserializerKinds.json
        )

    def test_event_to_json_excludes_private_fields(self):
        request_body = "str-body"
        event = nuclio_sdk.Event(body=request_body)
        event._private_field = 1
        event_obj = json.loads(event.to_json())
        assert "body" in event_obj
        assert "_private_field" not in event_obj
