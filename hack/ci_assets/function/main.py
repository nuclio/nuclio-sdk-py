# Copyright 2017 The Nuclio Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pkg_resources
import http
import json

import nuclio_sdk


def handler(context: nuclio_sdk.Context, event: nuclio_sdk.Event):
    headers = {
        ensure_str(header): ensure_str(value)
        for header, value in event.headers.items()
    }
    context.logger.debug_with(
        "Received request",
        event=json.dumps(
            {
                "id": event.id,
                "eventType": event.trigger.kind,
                "contentType": event.content_type,
                "headers": headers,
                "timestamp": event.timestamp.isoformat("T") + "Z",
                "path": event.path,
                "url": event.url,
                "method": event.method,
                "type": event.type,
                "typeVersion": event.type_version,
                "version": event.version,
                "body": event.body
                if isinstance(event.body, dict)
                else event.body.decode("utf8"),
            },
            default=json_default,
        ),
    )
    return context.Response(
        headers=headers,
        body={
            "sdk_version": get_sdk_version(),
        },
        content_type=event.content_type,
        status_code=http.HTTPStatus.OK,
    )


def get_sdk_version():
    return pkg_resources.get_distribution("nuclio_sdk").version


def json_default(s):
    if type(s) is bytes:
        return ensure_str(s)
    return s


def ensure_str(s, encoding="utf-8", errors="strict"):

    # Optimization: Fast return for the common case.
    if type(s) is str:
        return s
    if isinstance(s, bytes):
        return s.decode(encoding, errors)
    raise TypeError(f"not expecting type '{type(s)}'")
