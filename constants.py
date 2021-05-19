import pprint

class O(object):
    '''This helper class provides property access (the "dot notation")
    to the json object, backed by the original object stored in the _raw
    field.
    '''

    def __init__(self, raw):
        self._raw = raw

    def __getattr__(self, key):
        if key in self._raw:
            return self._raw[key]
        else:
            return super().__getattribute__(key)

    def __repr__(self):
        return '{name}({raw})'.format(
            name=self.__class__.__name__,
            raw=pprint.pformat(self._raw, indent=4),
        )


#DynamoDB Table Names
TABLE_NAMES = O({
    "DESTINATIONS": 'destinations',
    "PLACES": 'places',
    "ALBUMS": 'albums',
    "PHOTOS": 'photos'
})

#DynamoDB Table Keys
TABLE_KEYS = O({
    "DESTINATIONS": O({
        "PARTITION_KEY": "destination_id"
    }),
    "PLACES": O({
        "PARTITION_KEY": "destination_id",
        "SORT_KEY": "place_id"
    }),
    "ALBUMS": O({
        "PARTITION_KEY": "destination_id",
        "SORT_KEY": "place_id",
    }),
    "PHOTOS": O({
        "PARTITION_KEY": "place_id",
        "SORT_KEY": "photo_id"
    })
})

