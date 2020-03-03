import datetime

import nuclio_sdk.helpers

if nuclio_sdk.helpers.PYTHON2:
    import simplejson as json


    class JSONEncoder(json.JSONEncoder):

        """JSON encoder that can encode custom stuff"""

        def default(self, obj):
            if isinstance(obj, (datetime.datetime, datetime.date)):
                return obj.isoformat()

            # Let the base class default method raise the TypeError
            return json.JSONEncoder.default(self, obj)


    encoder_base_class = JSONEncoder

else:
    import orjson as json


    class JSONEncoder(object):
        def __init__(self, *args, **kwargs):
            pass

        def encode(self, o):
            return json.dumps(o, default=self.default).decode('utf-8')

        def default(self, obj):
            if isinstance(obj, bytes):
                return obj.decode('utf-8')

            # default method raise the TypeError
            raise TypeError


    encoder_base_class = JSONEncoder


class Encoder(encoder_base_class):
    def __init__(self, *args, **kwargs):

        # omit spaces after : \ ,
        if not kwargs.get('separators', None):
            kwargs['separators'] = (',', ':')
        super(Encoder, self).__init__(*args, **kwargs)
