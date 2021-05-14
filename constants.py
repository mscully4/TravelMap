import pprint
class Entity(object):
    '''This helper class provides property access (the "dot notation")
    to the json object, backed by the original object stored in the _raw
    field.
    '''

    def __init__(self, raw):
        self._raw = raw

    def __getattr__(self, key):
        print(key)
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
TABLE_NAMES = Entity({
    "CITIES": 'cities',
    "PLACES": 'places',
    "ALBUMS": 'albums',
    "PHOTOS": 'photos'
})

#DynamoDB Table Keys
TABLE_KEYS = Entity({
    "CITIES": Entity({
        "PARTITION_KEY": "place_id"
    }),
    "PLACES": Entity({
        "PARTITION_KEY": "city_id",
        "SORT_KEY": "place_id"
    }),
    "ALBUMS": Entity({
        "PARTITION_KEY": "place_id",
        "SORT_KEY": "album_id",
    }),
    "PHOTOS": Entity({
        "PARTITION_KEY": "place_id",
        "SORT_KEY": "photo_id"
    })
})

