import pprint
from decimal import Decimal

class Album(object):
    def __init__(self, destination_id, place_id, album_id=None, cover_photo_id=None, title=None, **kwargs):
        self.destination_id = destination_id
        self.place_id = place_id
        self.album_id = album_id if album_id else kwargs.get("id", None)
        self.cover_photo_id = cover_photo_id if cover_photo_id else kwargs.get("coverPhotoMediaItemId", None)
        self.title = title
        self.cover_photo_download_url = kwargs.get('coverPhotoBaseUrl', "")
        self.cover_photo_src = None 

    def __repr__(self):
        return '{name}({raw})'.format(
            name=self.__class__.__name__,
            raw=pprint.pformat(self.__dict__, indent=4),
        )

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
            "cover_photo_src": self.cover_photo_src,
            "title": self.title
        }