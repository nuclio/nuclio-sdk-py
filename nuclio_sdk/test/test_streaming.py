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
async def test_from_entrypoint_output_async_streaming(is_async, yield_as_response):
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

    else:

        def gen():
            for val in values:
                yield val

    generator = gen()
    encoder = json_encoder.Encoder()

    output_chunks = []
    async for chunk in Response.from_entrypoint_output_async(encoder, generator):
        output_chunks.append(chunk)

    # First chunk should be a full response
    first_expected_body = "first"
    first_chunk = output_chunks[0]
    assert isinstance(first_chunk, dict)
    assert first_chunk["body"] == first_expected_body
    assert first_chunk["status_code"] == (206 if yield_as_response else 200)
    assert first_chunk["content_type"] == (
        "text/custom" if yield_as_response else "text/plain"
    )
    if yield_as_response:
        assert first_chunk["headers"]["x-my-header"] == "test"

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
