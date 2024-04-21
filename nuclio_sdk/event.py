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

import enum
import base64
import sys
import json
import datetime

import nuclio_sdk


class _EventDeserializer(object):
    def deserialize(self, event_message):
        raise NotImplementedError

    @staticmethod
    def _try_deserialize_json(body):
        try:
            return json.loads(body.decode("utf-8"))
        except Exception as exc:
            # newline to force flush
            # NOTE: processor runs sdk with `-u` which means stderr is unbuffered which needs manual flushing
            sys.stderr.write(
                "Failed deserializing json body, error message: {0}\n".format(str(exc))
            )
        return body

    @staticmethod
    def _from_parsed_data(parsed_data, body):
        trigger = TriggerInfo(
            parsed_data["trigger"]["kind"], parsed_data["trigger"]["name"]
        )
        return Event(
            body=body,
            content_type=parsed_data["content_type"],
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
            offset=parsed_data.get("offset", 0),
            topic=parsed_data.get("topic"),
        )

    @staticmethod
    def _from_parsed_data_bytes(parsed_data, body):
        trigger = TriggerInfo(
            parsed_data[b"trigger"][b"kind"], parsed_data[b"trigger"][b"name"]
        )
        return Event(
            body=body,
            content_type=parsed_data[b"content_type"],
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
            offset=parsed_data.get(b"offset", 0),
            topic=parsed_data.get(b"topic"),
        )

    @staticmethod
    def decode_single_or_list_event(parsed_data, decode_single_event_function):
        if isinstance(parsed_data, list):
            return [
                decode_single_event_function(single_event_data)
                for single_event_data in parsed_data
            ]
        else:
            return decode_single_event_function(parsed_data)


class _EventDeserializerMsgPack(_EventDeserializer):
    def __init__(self, raw=False):
        # return the concrete function that handled raw/decoded event messages
        # pre-assign to avoid if/else during event processing
        self._from_msgpack_handler = (
            self._from_msgpack_raw if raw else self._from_msgpack_decoded
        )

    def deserialize(self, event_message):
        return self._from_msgpack_handler(event_message)

    def _from_msgpack_raw(self, parsed_data):
        def _decode_single_event(single_event_data):
            event_body = single_event_data[b"body"]
            if single_event_data[b"content_type"] == b"application/json":
                event_body = _EventDeserializer._try_deserialize_json(event_body)
            return _EventDeserializer._from_parsed_data_bytes(
                single_event_data, event_body
            )

        return self.decode_single_or_list_event(parsed_data, _decode_single_event)

    def _from_msgpack_decoded(self, parsed_data):
        def _decode_single_event(single_event_data):
            event_body = single_event_data["body"]
            if single_event_data["content_type"] == "application/json":
                event_body = _EventDeserializer._try_deserialize_json(event_body)
            return _EventDeserializer._from_parsed_data(single_event_data, event_body)

        return self.decode_single_or_list_event(parsed_data, _decode_single_event)


class _EventDeserializerJSON(_EventDeserializer):
    def deserialize(self, event_message):
        parsed_data = json.loads(event_message)

        def _deserialize_single_event(single_event):
            body = single_event["body"]
            if single_event["content_type"] == "application/json" and not isinstance(
                body, dict
            ):
                body = _EventDeserializer._try_deserialize_json(body)
            return _EventDeserializer._from_parsed_data(single_event, body)

        return self.decode_single_or_list_event(parsed_data, _deserialize_single_event)


class EventDeserializerKinds(enum.Enum):
    msgpack = _EventDeserializerMsgPack(raw=False)
    msgpack_raw = _EventDeserializerMsgPack(raw=True)
    json = _EventDeserializerJSON()


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
        topic=None,
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
        self.topic = topic

    def to_json(self):
        obj = {}
        for field_name, field_value in vars(self).items():
            # exclude private fields
            if not field_name.startswith("_"):
                obj[field_name] = field_value
        obj["trigger"] = {
            "kind": self.trigger.kind,
            "name": self.trigger.name,
        }

        # serialize it if is a datetime object
        if isinstance(self.timestamp, datetime.datetime):
            obj["timestamp"] = str(self.timestamp)

        if isinstance(obj["body"], bytes):
            obj["body"] = base64.b64encode(obj["body"]).decode("ascii")

        return json.dumps(obj, default=str)

    def get_header(self, header_key):
        for key, value in self.headers.items():
            if key.lower() == header_key.lower():
                return value

    @staticmethod
    def from_msgpack(data):
        """
        Deprecated.
        Use instead: Event.deserialize(data, kind=EventDeserializerKinds.msgpack)
        NOTE: To be removed on >= 0.4.0
        """
        return Event.deserialize(data, kind=EventDeserializerKinds.msgpack)

    @staticmethod
    def from_json(data):
        """
        Deprecated.
        Use instead: Event.deserialize(data, kind=EventDeserializerKinds.json)
        NOTE: To be removed on >= 0.4.0
        """
        return Event.deserialize(data, kind=EventDeserializerKinds.json)

    @classmethod
    def deserialize(cls, data, kind=EventDeserializerKinds.msgpack_raw):
        """
        Deserialize event message
        """
        return kind.value.deserialize(data)

    def compile_explicit_ack_message(self):
        """
        Return json of offset data
        """
        return nuclio_sdk.QualifiedOffset.from_event(
            self
        ).compile_explicit_ack_message()

    def __repr__(self):
        return self.to_json()
