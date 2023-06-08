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

import nuclio_sdk.test
import nuclio_sdk.json_encoder
import nuclio_sdk.helpers


class TestResponse(nuclio_sdk.test.TestCase):
    def setUp(self):
        self._encoder = nuclio_sdk.json_encoder.Encoder()

    def test_str(self):
        handler_return = "test"
        expected_response = self._compile_output_response(body="test")
        self._validate_response(handler_return, expected_response)

    def test_int(self):
        handler_return = 2020
        expected_response = self._compile_output_response(body="2020")
        self._validate_response(handler_return, expected_response)

    def test_float(self):
        handler_return = 12.34
        expected_response = self._compile_output_response(body="12.34")
        self._validate_response(handler_return, expected_response)

    def test_bytes(self):
        handler_return = b"test"
        expected_response = self._compile_output_response(
            body="dGVzdA==", body_encoding="base64"  # base64 value for 'test'
        )
        self._validate_response(handler_return, expected_response)

    def test_dict(self):
        handler_return = {"json": True}
        expected_response = self._compile_output_response(
            body='{"json": true}', content_type="application/json"
        )
        self._validate_response(handler_return, expected_response)

    def test_iterable(self):
        handler_return = [1, 2, 3, True]
        expected_response = self._compile_output_response(
            body="[1, 2, 3, true]", content_type="application/json"
        )
        self._validate_response(handler_return, expected_response)

    def test_datetime(self):
        handler_return = datetime.datetime.now()
        expected_response = self._compile_output_response(body=str(handler_return))
        self._validate_response(handler_return, expected_response)

    def test_status_code_and_str(self):
        handler_return = (201, "test")
        expected_response = self._compile_output_response(
            body="test", status_code=handler_return[0]
        )
        self._validate_response(handler_return, expected_response)

    def test_status_code_and_dict(self):
        handler_return = (201, {"json": True})
        expected_response = self._compile_output_response(
            body='{"json": true}',
            status_code=handler_return[0],
            content_type="application/json",
        )
        self._validate_response(handler_return, expected_response)

    def test_sdk_response_str(self):
        handler_return = nuclio_sdk.Response(body="test")
        expected_response = self._compile_output_response(body="test")
        self._validate_response(handler_return, expected_response)

    def test_sdk_response_dict(self):
        handler_return = {"json": True}
        expected_response = self._compile_output_response(
            body='{"json": true}', content_type="application/json"
        )
        self._validate_response(handler_return, expected_response)

    def _validate_response(self, handler_return, expected_response):
        response = nuclio_sdk.Response.from_entrypoint_output(
            self._encoder.encode, handler_return
        )
        self.assertDictEqual(response, expected_response)

    def _compile_output_response(self, **kwargs):
        return {**nuclio_sdk.Response.empty_response(), **kwargs}
