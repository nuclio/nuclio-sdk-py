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


class QualifiedOffset(object):
    def __init__(self, topic, partition, offset):
        self.topic = topic
        self.partition = partition
        self.offset = offset

    @staticmethod
    def from_event(event):
        # topic resolving required to keep BC (NUC-233)
        topic = event.topic if event.topic else event.path
        return QualifiedOffset(topic, event.shard_id, event.offset)

    def compile_explicit_ack_message(self):
        """
        Return a stream ack message with json of offset data
        """
        return {
            "kind": "streamMessageAck",
            "attributes": {
                "topic": self.topic,
                "partition": self.partition,
                "offset": self.offset,
            },
        }
