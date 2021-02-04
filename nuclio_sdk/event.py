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

import base64
import sys
import json
import datetime


class TriggerInfo(object):
    def __init__(self, kind="", name=""):
        self.kind = kind
        self.name = name


class Event(object):
    def __init__(
        self,
        body=None,
        content_type=None,
        trigger=None,
        fields=None,
        headers=None,
        _id=None,
        method=None,
        path=None,
        size=None,
        timestamp=None,
        url=None,
        shard_id=None,
        num_shards=None,
        _type=None,
        type_version=None,
        version=None,
        last_in_batch=None,
        offset=None,
    ):
        self.body = body
        self.content_type = content_type
        self.trigger = trigger or TriggerInfo()
        self.fields = fields or {}
        self.headers = headers or {}
        self.id = _id
        self.method = method
        self.path = path or "/"
        self.size = size
        self.timestamp = timestamp or 0
        self.url = url
        self.shard_id = shard_id
        self.num_shards = num_shards
        self.type = _type
        self.type_version = type_version
        self.version = version
        self.last_in_batch = last_in_batch or False
        self.offset = offset or 0

    def to_json(self):
        obj = vars(self).copy()
        obj["trigger"] = {
            "kind": self.trigger.kind,
            "name": self.trigger.name,
        }

        # serialize it if is a datetime object
        if isinstance(self.timestamp, datetime.datetime):
            obj["timestamp"] = str(self.timestamp)

        if isinstance(obj["body"], bytes):
            obj["body"] = base64.b64encode(obj["body"]).decode("ascii")

        return json.dumps(obj)

    def get_header(self, header_key):
        for key, value in self.headers.items():
            if key.lower() == header_key.lower():
                return value

    @staticmethod
    def from_msgpack(parsed_data):
        """
        Deprecated. use nuclio_sdk.event.EventSerializerFactory.create("msgpack").serialize(parsed_data) instead.
        To be removed on >= 0.4.0
        """
        return EventSerializerFactory.create("msgpack").serialize(parsed_data)

    @staticmethod
    def from_json(data):
        """
        Deprecated. use nuclio_sdk.event.EventSerializerFactory.create("json").serialize(data) instead.
        To be removed on >= 0.4.0
        """
        return EventSerializerFactory.create("json").serialize(data)

    @classmethod
    def from_parsed_data(cls, parsed_data, body, content_type):
        trigger = TriggerInfo(
            parsed_data["trigger"]["kind"], parsed_data["trigger"]["name"]
        )
        return cls(
            body=body,
            content_type=content_type,
            trigger=trigger,
            fields=parsed_data["fields"],
            headers=parsed_data["headers"],
            _id=parsed_data["id"],
            method=parsed_data["method"],
            path=parsed_data["path"],
            size=parsed_data["size"],
            timestamp=datetime.datetime.utcfromtimestamp(parsed_data["timestamp"]),
            url=parsed_data["url"],
            shard_id=parsed_data["shard_id"],
            num_shards=parsed_data["num_shards"],
            _type=parsed_data["type"],
            type_version=parsed_data["type_version"],
            version=parsed_data["version"],
        )

    @classmethod
    def from_parsed_data_bytes(cls, parsed_data, body, content_type):
        trigger = TriggerInfo(
            parsed_data[b"trigger"][b"kind"], parsed_data[b"trigger"][b"name"]
        )
        return cls(
            body=body,
            content_type=content_type,
            trigger=trigger,
            fields=parsed_data[b"fields"],
            headers=parsed_data[b"headers"],
            _id=parsed_data[b"id"],
            method=parsed_data[b"method"],
            path=parsed_data[b"path"],
            size=parsed_data[b"size"],
            timestamp=datetime.datetime.utcfromtimestamp(parsed_data[b"timestamp"]),
            url=parsed_data[b"url"],
            shard_id=parsed_data[b"shard_id"],
            num_shards=parsed_data[b"num_shards"],
            _type=parsed_data[b"type"],
            type_version=parsed_data[b"type_version"],
            version=parsed_data[b"version"],
        )

    def __repr__(self):
        return self.to_json()


class EventSerializer(object):
    def serialize(self, event_message) -> Event:
        raise NotImplementedError


class EventSerializerFactory(object):
    @staticmethod
    def create(serializer_kind, runtime_version="3.6") -> EventSerializer:
        if serializer_kind == "msgpack":
            return _EventSerializerMsgPack(raw=runtime_version != "3.6")
        if serializer_kind == "json":
            return _EventSerializerJSON()
        raise RuntimeError(f"No such serializer kind {serializer_kind}")


class _EventSerializerMsgPack(EventSerializer):
    def __init__(self, raw=False):

        # return the concrete function that handled raw/decoded event messages
        # pre-assign to avoid if/else during event processing
        self._from_msgpack_handler = (
            self._from_msgpack_raw if raw else self._from_msgpack_decoded
        )

    def serialize(self, event_message):
        return self._from_msgpack_handler(event_message)

    def _from_msgpack_raw(self, parsed_data):
        content_type = parsed_data[b"content_type"]
        body = self._decode_body(parsed_data[b"body"], content_type)
        return Event.from_parsed_data_bytes(parsed_data, body, content_type)

    def _from_msgpack_decoded(self, parsed_data):
        content_type = parsed_data["content_type"]
        body = self._decode_body(parsed_data["body"], content_type)
        return Event.from_parsed_data(parsed_data, body, content_type)

    def _decode_body(self, body, content_type):
        if content_type == "application/json":
            try:
                return json.loads(body.decode("utf-8"))
            except Exception as exc:
                sys.stderr.write(str(exc))

        return body


class _EventSerializerJSON(EventSerializer):
    def serialize(self, event_message):
        parsed_data = json.loads(event_message)

        # extract content type, needed to decode body
        content_type = parsed_data["content_type"]
        body = self._decode_body(parsed_data["body"], content_type)
        return Event.from_parsed_data(parsed_data, body, content_type)

    def _decode_body(self, body, content_type):
        if isinstance(body, dict):
            return body

        try:
            decoded_body = base64.b64decode(body)
        except:  # noqa E722
            return body

        if content_type == "application/json":
            try:
                return json.loads(decoded_body)
            except:  # noqa E722
                pass

        return decoded_body
