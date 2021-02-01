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

import nuclio_sdk


def handler(context: nuclio_sdk.Context, event: nuclio_sdk.Event):
    context.logger.debug_with("Received request", event=event.to_json())
    return context.Response(
        headers=event.headers,
        body={
            "sdk_version": get_sdk_version(),
        },
        content_type=event.content_type,
        status_code=http.HTTPStatus.OK,
    )


def get_sdk_version():
    return pkg_resources.get_distribution("nuclio_sdk").version
