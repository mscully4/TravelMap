import pprint
from decimal import Decimal
from DynamoDB import _put_item, _delete_item

class Place(object):
    '''This helper class provides property access (the "dot notation")
    to the json object, backed by the original object stored in the _raw
    field.
    '''

    def __init__(self, name, address, city, state, country, zip_code, latitude, longitude, place_id, city_id):
        self.name = name
        self.address = address 
        self.city = city 
        self.state = state
        self.country = country 
        self.zip_code = zip_code 
        self.latitude = latitude 
        self.longitude = longitude 
        self.place_id = place_id
        self.city_id = city_id

    # def __getattr__(self, key):
    #     if key in self._raw:
    #         return self._raw[key]
    #     else:
    #         return super().__getattribute__(key)
    

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
    def insert(self, table):
        _put_item(table, self.serialize())

    def update(self, table):
        _put_item(table, self.serialize())
    
    def delete(self, table):
        key = {
            "place_id": self.place_id
        }
        _delete_item(table, key)

    def serialize(self):
        return {
            "place_id": self.place_id,
            "name": self.name,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "zip_code": self.zip_code,
            "latitude": Decimal(str(self.latitude)),
            "longitude": Decimal(str(self.longitude)),
            "city_id": self.city_id
        }