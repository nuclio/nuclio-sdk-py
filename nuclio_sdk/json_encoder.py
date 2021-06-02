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

import json
import json.encoder


# JSON encoder that can encode custom stuff
class Encoder(json.JSONEncoder):
    def __init__(self, **kwargs):
        super(Encoder, self).__init__(**kwargs)
        self.nan_str = "NaN"

    def iterencode(self, o, _one_shot=False):
        """
        Encode the given object and yield each string
        representation as available.

        For example::

            for chunk in JSONEncoder().iterencode(bigobject):
                mysocket.write(chunk)

        """
        if self.check_circular:
            markers = {}
        else:
            markers = None
        if self.ensure_ascii:
            _encoder = json.encoder.encode_basestring_ascii
        else:
            _encoder = json.encoder.encode_basestring

        def floatstr(
            o,
            allow_nan=self.allow_nan,
            nan_str=self.nan_str,
            _repr=float.__repr__,
            _inf=json.encoder.INFINITY,
            _neginf=-json.encoder.INFINITY,
        ):
            if o != o:
                text = '"{0}"'.format(nan_str)
            elif o == _inf:
                text = '"Infinity"'
            elif o == _neginf:
                text = '"-Infinity"'
            else:
                return _repr(o)

            if not allow_nan:
                raise ValueError(
                    "Out of range float values are not JSON compliant: " + repr(o)
                )

            return text

        _iterencode = json.encoder._make_iterencode(
            markers,
            self.default,
            _encoder,
            self.indent,
            floatstr,
            self.key_separator,
            self.item_separator,
            self.sort_keys,
            self.skipkeys,
            _one_shot,
        )
        return _iterencode(o, 0)

    def default(self, obj):

        # EAFP all the way. Leave the unused "exc" in for debugging ease
        try:
            return obj.__log__()
        except Exception as exc:  # noqa
            try:
                return obj.__repr__()
            except Exception as exc:  # noqa
                try:
                    return str(obj)
                except Exception as exc:
                    return "Unable to serialize object: {0}".format(exc)
