import googlemaps as gm

class GoogleMaps(object):
    def __init__(self, api_key):
        self.gm = gm.Client(key=api_key)

    def get_destination_suggestions(self, text):
        '''
        A method for autocompleting city names given a text entry

        Arguments:
            text <str>: A city name
        '''
        res = self.gm.places_autocomplete(text, types=['(cities)'])
        self.suggestions = res 
        return res 

    def get_place_suggestions(self, text, location=None, radius=25000):
        '''
        A method for autocompleting places given a text entry

        Arguments:
            text <str>: A place name
            location <list>: A list of lat, long coordinates
            radius <str>: The radius from location to focus the search on 
        '''
        res = self.gm.places_autocomplete(text, location=location, radius=radius)
        return res        

    def geocode_destination(self, place_id):
        '''
        A method for retrieving information about a city given its place_id

        Arguments:
            place_id <str>: Google Map's generated unique identifier

        Returns:
            <dict>: A dictionary containing information about a city (country, country_code, coordinates, etc)
        '''
        s = self.gm.reverse_geocode(place_id)[0]

        for comp in s['address_components']:
            if 'country' in comp['types']:
                country = comp['long_name']
                country_code = comp['short_name']

        data = {
            'name': s['address_components'][0]['long_name'],
            'country': country,
            'country_code': country_code,
            'latitude': s['geometry']['location']['lat'],
            'longitude': s['geometry']['location']['lng'],
            'destination_id': place_id
        }
        return data

    def geocode_place(self, ac):
        '''
        A method for retrieving information about a place given its place_id

        Arguments:
            place_id <str>: Google Map's generated unique identifier

        Returns:
            <dict>: A dictionary containing information about a place (address, city, country, coordinates, etc)
        '''
        s = self.gm.reverse_geocode(ac['place_id'])[0]

        country, zip_code, street, street_number, state, city = '', '', '', '', '', ''
        for comp in s['address_components']:
            if 'country' in comp['types']:
                country = comp['long_name']
            elif 'postal_code' in comp['types']:
                zip_code = comp['long_name']
            elif 'street_number' in comp['types']:
                street_number = comp['long_name']
            elif 'route' in comp['types']:
                street = comp['long_name']
            elif 'locality' in comp['types']:
                city = comp['long_name']
            elif "administrative_area_level_1" in comp['types']:
                state = comp['long_name']

        return {
            'name': ac['structured_formatting']['main_text'],
            'place_id': ac['place_id'],
            'address': street + " " + street_number,
            'city': city,
            'state': state,
            'country': country,
            'zip_code': zip_code,
            'latitude': s['geometry']['location']['lat'],
            'longitude': s['geometry']['location']['lng']
        }
