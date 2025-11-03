import base64
import pytest
from nuclio_sdk import (
    Response,
    json_encoder,
    GENERATOR_RESPONSE,
    RESPONSE_WITH_GENERATOR_BODY,
    SINGLE_RESPONSE,
)


@pytest.mark.asyncio
@pytest.mark.parametrize("is_async", [False, True])
@pytest.mark.parametrize("yield_as_response", [False, True])
@pytest.mark.parametrize("result_as_response_with_gen", [False, True])
async def test_from_entrypoint_output_async_streaming(
    is_async, yield_as_response, result_as_response_with_gen
):
    def make_response(body):
        return Response(
            body=body,
            content_type="text/custom",
            status_code=206,
            headers={"x-my-header": "test"},
        )

    # Set up sync or async generator with str, bytes, and newline-containing data
    items = ["first", "second\nchunk", b"final bytes"]
    values = [make_response(i) if yield_as_response else i for i in items]

    if is_async:

        async def gen():
            for val in values:
                yield val

        async def body_gen():
            return Response(
                body=gen(),
                content_type="text/response",
                status_code=201,
                headers={"x-my-header": "test1"},
            )

        generator = gen() if not result_as_response_with_gen else await body_gen()
    else:

        def gen():
            for val in values:
                yield val

        def body_gen():
            return Response(
                body=gen(),
                content_type="text/response",
                status_code=201,
                headers={"x-my-header": "test1"},
            )

        generator = gen() if not result_as_response_with_gen else body_gen()

    encoder = json_encoder.Encoder()
    output_chunks = []
    async for chunk in Response.from_entrypoint_output_async(encoder, generator):
        output_chunks.append(chunk)

    if result_as_response_with_gen:
        expected_status_code = 201
        expected_content_type = "text/response"
        expected_headers = {"x-my-header": "test1"}
    elif yield_as_response:
        expected_status_code = 206
        expected_content_type = "text/custom"
        expected_headers = {"x-my-header": "test"}
    else:
        expected_status_code = 200
        expected_content_type = "text/plain"
        expected_headers = {}

    # First chunk should be a full response
    first_expected_body = "first"
    first_chunk = output_chunks[0]
    assert isinstance(first_chunk, dict)
    assert first_chunk["body"] == first_expected_body
    assert first_chunk["status_code"] == expected_status_code
    assert first_chunk["content_type"] == expected_content_type
    assert first_chunk["headers"] == expected_headers

    # Remaining chunks should be base64-encoded body values
    for i, raw in enumerate(items[1:], start=1):
        expected_encoded = base64.b64encode(
            raw.encode() if isinstance(raw, str) else raw
        ).decode("ascii")
        assert output_chunks[i] == expected_encoded


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async", [False, True])
def test_get_handler_output_type(use_async):
    # Create sync or async generator
    if use_async:

        async def async_gen():
            yield 1

        gen = async_gen()
    else:

        def sync_gen():
            yield 1

        gen = sync_gen()

    # Case 1: handler_output is a generator itself
    assert Response.get_handler_output_type(gen) == GENERATOR_RESPONSE

    # Case 2: handler_output is a Response with generator body
    response = Response(body=gen)
    assert Response.get_handler_output_type(response) == RESPONSE_WITH_GENERATOR_BODY

    # Case 3: handler_output is a plain Response with non-generator body
    response = Response(body="non-generator body")
    assert Response.get_handler_output_type(response) == SINGLE_RESPONSE

    # Case 4: handler_output is something else (e.g., string)
    assert Response.get_handler_output_type("hello") == SINGLE_RESPONSE
    assert Response.get_handler_output_type(123) == SINGLE_RESPONSE
