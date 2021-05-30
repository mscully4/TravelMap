import pprint
from decimal import Decimal

class Destination(object):
    def __init__(self, country, country_code, latitude, longitude, destination_id=None, name=None, **kwargs):
        self.destination_id = destination_id if destination_id else kwargs.get("place_id")
        self.name = name
        self.country = country
        self.country_code = country_code
        self.latitude = latitude
        self.longitude = longitude
        self.type = kwargs.get('type', '')

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
            "name": self.name,
            "country": self.country,
            "country_code": self.country_code,
            "latitude": Decimal(str(self.latitude)),
            "longitude": Decimal(str(self.longitude)),
            "type": self.type
        }