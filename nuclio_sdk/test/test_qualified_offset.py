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


class TestQualifiedOffset(nuclio_sdk.test.TestCase):
    def test_from_event(self):
        event = nuclio_sdk.Event(path="path", shard_id="shard_id", offset="offset")
        expected_qualified_offset = nuclio_sdk.QualifiedOffset(
            topic="path", partition="shard_id", offset="offset"
        )
        actual_qualified_offset = nuclio_sdk.QualifiedOffset.from_event(event)
        self._check_equal_qualified_offsets(
            expected_qualified_offset, actual_qualified_offset
        )

    def test_compile_explicit_ack_message(self):
        event = nuclio_sdk.Event(path="path", shard_id="shard_id", offset="offset")
        qualified_offset = nuclio_sdk.QualifiedOffset.from_event(event)
        expected_explicit_ack_message = {
            "kind": "streamMessageAck",
            "attributes": {
                "topic": "path",
                "partition": "shard_id",
                "offset": "offset",
            },
        }
        actual_explicit_ack_message = qualified_offset.compile_explicit_ack_message()
        self.assertEqual(expected_explicit_ack_message, actual_explicit_ack_message)

        # check that if topic is passed, it takes precedence
        event.topic = "topic"
        expected_explicit_ack_message["attributes"]["topic"] = "topic"
        qualified_offset = nuclio_sdk.QualifiedOffset.from_event(event)
        actual_explicit_ack_message = qualified_offset.compile_explicit_ack_message()
        self.assertEqual(expected_explicit_ack_message, actual_explicit_ack_message)

    def _check_equal_qualified_offsets(self, expected, actual):
        self.assertEqual(expected.topic, actual.topic)
        self.assertEqual(expected.partition, actual.partition)
        self.assertEqual(expected.offset, actual.offset)
