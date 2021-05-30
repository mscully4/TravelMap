import pprint
from decimal import Decimal

class Place(object):
    def __init__(self, name, address, state, country, zip_code, latitude, longitude, place_id, destination_id, city=None, **kwargs):
        self.place_id = place_id
        self.name = name
        self.address = address 
        self.city = city if city else kwargs.get('destination', None)
        self.state = state
        self.country = country 
        self.zip_code = zip_code 
        self.latitude = latitude 
        self.longitude = longitude 
        self.destination_id = destination_id

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
            "destination_id": self.destination_id
        }