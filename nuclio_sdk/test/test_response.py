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

import asyncio
import base64
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

    def test_response_with_event_id(self):
        handler_return = nuclio_sdk.Response(body="test", event_id="1337")
        expected_response = self._compile_output_response(body="test", event_id="1337")
        self._validate_response(handler_return, expected_response)

    def test_generator_output_with_integers(self):
        """Regression test: yielding integers from a generator should not crash
        with 'int is not a bytes-like object' on subsequent chunks."""

        def int_generator():
            for i in range(1, 4):
                yield i

        results = asyncio.run(self._collect_generator_output(int_generator()))

        # First item goes through from_entrypoint_output (returns a dict response)
        self.assertIsInstance(results[0], dict)
        self.assertEqual(results[0]["body"], "1")

        # Subsequent items are base64-encoded strings
        for idx, value in enumerate([2, 3], start=1):
            expected_encoded = base64.b64encode(str(value).encode()).decode("ascii")
            self.assertEqual(results[idx], expected_encoded)

    def test_generator_output_with_strings(self):
        def str_generator():
            yield "first"
            yield "second"

        results = asyncio.run(self._collect_generator_output(str_generator()))

        self.assertIsInstance(results[0], dict)
        self.assertEqual(results[0]["body"], "first")

        expected_encoded = base64.b64encode(b"second").decode("ascii")
        self.assertEqual(results[1], expected_encoded)

    def test_generator_output_with_bytes(self):
        def bytes_generator():
            yield b"first"
            yield b"second"

        results = asyncio.run(self._collect_generator_output(bytes_generator()))

        self.assertIsInstance(results[0], dict)
        # First item goes through from_entrypoint_output which base64-encodes bytes
        self.assertEqual(results[0]["body"], base64.b64encode(b"first").decode("ascii"))

        expected_encoded = base64.b64encode(b"second").decode("ascii")
        self.assertEqual(results[1], expected_encoded)

    def test_generator_output_with_mixed_types(self):
        """Verify generator handles a mix of str, int, float, and bytes."""

        def mixed_generator():
            yield "hello"
            yield 42
            yield 3.14
            yield b"raw"

        results = asyncio.run(self._collect_generator_output(mixed_generator()))

        self.assertIsInstance(results[0], dict)
        self.assertEqual(results[0]["body"], "hello")

        self.assertEqual(results[1], base64.b64encode(b"42").decode("ascii"))
        self.assertEqual(results[2], base64.b64encode(b"3.14").decode("ascii"))
        self.assertEqual(results[3], base64.b64encode(b"raw").decode("ascii"))

    def test_generator_output_with_response_object(self):
        """Verify that when a Response object wraps a generator body,
        the first chunk inherits headers/status from the Response."""

        def body_generator():
            yield "chunk1"
            yield "chunk2"
            yield 99

        response_object = nuclio_sdk.Response(
            headers={"X-Custom": "header"},
            body=body_generator(),
            content_type="text/html",
            status_code=201,
        )

        results = asyncio.run(
            self._collect_generator_output(
                response_object.body, response_object=response_object
            )
        )

        # First chunk inherits headers, status, content_type from the Response object
        self.assertIsInstance(results[0], dict)
        self.assertEqual(results[0]["body"], "chunk1")
        self.assertEqual(results[0]["status_code"], 201)
        self.assertEqual(results[0]["content_type"], "text/html")
        self.assertEqual(results[0]["headers"], {"X-Custom": "header"})

        # Subsequent chunks are base64-encoded
        self.assertEqual(results[1], base64.b64encode(b"chunk2").decode("ascii"))
        self.assertEqual(results[2], base64.b64encode(b"99").decode("ascii"))

    async def _collect_generator_output(self, generator, response_object=None):
        results = []
        async for chunk in nuclio_sdk.Response.from_generator_output(
            json_encoder=self._encoder.encode,
            body_generator=generator,
            response_object=response_object,
        ):
            results.append(chunk)
        return results

    def _validate_response(self, handler_return, expected_response):
        response = nuclio_sdk.Response.from_entrypoint_output(
            self._encoder.encode, handler_return
        )
        self.assertDictEqual(response, expected_response)

    def _compile_output_response(self, **kwargs):
        return {**nuclio_sdk.Response.empty_response(), **kwargs}
