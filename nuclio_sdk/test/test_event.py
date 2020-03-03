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

import nuclio_sdk.test
import nuclio_sdk.json


class TestEvent(nuclio_sdk.test.TestCase):
    def setUp(self):
        pass

    def test_event_to_json(self):
        event = nuclio_sdk.Event(body=b'bytes-body',
                                 content_type='content-type',
                                 trigger=nuclio_sdk.TriggerInfo(kind='http', name='my-http-trigger'),
                                 method='GET')
        event_json = event.to_json()
        serialized_event = nuclio_sdk.json.loads(event_json)
        self.assertEqual(serialized_event['body'], 'bytes-body')
        self.assertEqual(serialized_event['content_type'], 'content-type')
        self.assertEqual(serialized_event['method'], 'GET')
        self.assertEqual(serialized_event['trigger'], {'kind': 'http', 'name': 'my-http-trigger'})

    def test_event_to_json_string_body(self):
        event = nuclio_sdk.Event(body='bytes-body')
        jsonized_event = nuclio_sdk.json.loads(event.to_json())
        self.assertEqual(jsonized_event['body'], 'bytes-body')
