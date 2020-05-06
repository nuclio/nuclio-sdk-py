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

    def __init__(self, kind='', name=''):
        self.kind = kind
        self.name = name


class Event(object):

    def __init__(self,
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
                 offset=None):
        self.body = body
        self.content_type = content_type
        self.trigger = trigger or TriggerInfo()
        self.fields = fields or {}
        self.headers = headers or {}
        self.id = _id
        self.method = method
        self.path = path or '/'
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
        obj['trigger'] = {
            'kind': self.trigger.kind,
            'name': self.trigger.name
        }

        # serialize it if is a datetime object
        if isinstance(self.timestamp, datetime.datetime):
            obj['timestamp'] = str(self.timestamp)

        # TEMP: this should be done only on python3
        if isinstance(obj['body'], bytes):
            obj['body'] = base64.b64encode(obj['body']).decode('ascii')

        return json.dumps(obj)

    def get_header(self, header_key):
        for key, value in self.headers.items():
            if key.lower() == header_key.lower():
                return value

    @staticmethod
    def from_msgpack(parsed_data):
        """Decode msgpack event encoded as JSON by processor"""

        # extract content type, needed to decode body
        content_type = parsed_data['content_type']
        body = Event.decode_msgpack_body(parsed_data['body'], content_type)
        return Event.from_parsed_data(parsed_data, body, content_type)

    @staticmethod
    def from_json(data):
        """Decode event encoded as JSON by processor"""

        parsed_data = json.loads(data)

        # extract content type, needed to decode body
        content_type = parsed_data['content_type']
        body = Event.decode_body(parsed_data['body'], content_type)
        return Event.from_parsed_data(parsed_data, body, content_type)

    @classmethod
    def from_parsed_data(cls, parsed_data, body, content_type):
        trigger = TriggerInfo(
            parsed_data['trigger']['kind'],
            parsed_data['trigger']['name']
        )
        return cls(body=body,
                   content_type=content_type,
                   trigger=trigger,
                   fields=parsed_data.get('fields'),
                   headers=parsed_data.get('headers'),
                   _id=parsed_data['id'],
                   method=parsed_data['method'],
                   path=parsed_data['path'],
                   size=parsed_data['size'],
                   timestamp=datetime.datetime.utcfromtimestamp(parsed_data['timestamp']),
                   url=parsed_data['url'],
                   shard_id=parsed_data['shard_id'],
                   num_shards=parsed_data['num_shards'],
                   _type=parsed_data['type'],
                   type_version=parsed_data['type_version'],
                   version=parsed_data['version'])

    @staticmethod
    def decode_body(body, content_type):
        """Decode event body"""

        if isinstance(body, dict):
            return body

        try:
            decoded_body = base64.b64decode(body)
        except:  # noqa E722
            return body

        if content_type == 'application/json':
            try:
                return json.loads(decoded_body)
            except:  # noqa E722
                pass

        return decoded_body

    @staticmethod
    def decode_msgpack_body(body, content_type):
        """Decode msgpack event body"""

        if content_type == 'application/json':
            try:
                return json.loads(body.decode('utf-8'))
            except Exception as exc:
                sys.stderr.write(str(exc))

        return body

    def __repr__(self):
        return self.to_json()
