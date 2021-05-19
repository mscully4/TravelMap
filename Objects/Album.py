import pprint
from decimal import Decimal

class Album(object):
    '''
    This helper class provides property access (the "dot notation")
    to the json object, backed by the original object stored in the _raw
    field.
    '''

    def __init__(self, destination_id, place_id, album_id, cover_photo_id, title):
        self.destination_id = destination_id
        self.album_id = album_id
        self.place_id = place_id
        self.cover_photo_id = cover_photo_id
        self.title = title

    # def __repr__(self):
    #     return '{name}({raw})'.format(
    #         name=self.__class__.__name__,
    #         raw=pprint.pformat(self.__dict__, indent=4),
    #     )

    # @property
    # def city(self):
    #     return self._city
    
    # @city.setter
    # def city(self, city):
    #     if isinstance(city, str):
    #         self._city = city

    def serialize(self):
        return {
            "destination_id": self.destination_id,
            "place_id": self.place_id,
            "album_id": self.album_id,
            "cover_photo_id": self.cover_photo_id,
            "title": self.title
        }