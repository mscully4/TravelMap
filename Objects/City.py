import pprint
from decimal import Decimal
from DynamoDB import _put_item, _delete_item

class City(object):
    '''This helper class provides property access (the "dot notation")
    to the json object, backed by the original object stored in the _raw
    field.
    '''

    def __init__(self, city, country, country_code, latitude, longitude, place_id):
        self.city = city
        self.country = country
        self.country_code = country_code
        self.latitude = latitude
        self.longitude = longitude
        self.place_id = place_id

        # self.attrs = ["city", "country", "country_code", "latitude", "longitude", "place_id"]

    # def __getattr__(self, key):
    #     if key in self._raw:
    #         return self._raw[key]
    #     else:
    #         return super().__getattribute__(key)

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
            "place_id": self.place_id,
            "city": self.city,
            "country": self.country,
            "country_code": self.country_code,
            "latitude": Decimal(str(self.latitude)),
            "longitude": Decimal(str(self.longitude))
        }

    def insert(self, table):
        _put_item(table, self.serialize())

    def update(self, table):
        _put_item(table, self.serialize())
    
    def delete(self, table):
        key = {
            "place_id": self.place_id
        }
        _delete_item(table, key)