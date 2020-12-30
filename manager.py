from GooglePhotos import GooglePhotos
import utils as u

import googlemaps as gm
import json
import boto3
import requests
import hashlib  as hl
from PIL import Image
import io
import math
import os


class Manager(object):
    def __init__(self, bucket_name, file_name, gp):
        self.bucket_name = bucket_name
        self.file_name = file_name
        self.gp = gp

        self.s3_client = boto3.client('s3')
        self.s3_resource = boto3.resource('s3')
        self.s3_bucket = config['AWS']['BUCKET']
        self.s3_region = config['AWS']['REGION']
        self.s3_base = 'https://{}.s3.{}.amazonaws.com/'.format(self.s3_bucket, self.s3_region)
        
        self.gm = gm.Client(key=config['Google'].get('API_KEY'))

        self.data = self.read(self.file_name)
        self.cities = [city.get('place_id') for city in self.data['destinations']]
        self.places = [p.get('placeId') for city in self.data['destinations'] for p in city['places']]
        self.images = {city['city']: {place['name']: place['images'] for place in city['places']} for city in self.data['destinations']}

        self.run = True

        u.cls()

    def get_city_suggestions(self, text, types=None):
        return self.gm.places_autocomplete(text, types=['(cities)'])

    def get_place_suggestions(self, text, location=None, radius=None):
        return self.gm.places_autocomplete(text, location=location, radius=radius)

    def geocode_city(self, placeId):
        s = self.gm.reverse_geocode(placeId)[0]

        for comp in s['address_components']:
            if 'country' in comp['types']:
                country = comp['long_name']
                country_code = comp['short_name']

        data = {
            'city': s['address_components'][0]['long_name'],
            'country': country,
            'countryCode': country_code,
            'latitude': s['geometry']['location']['lat'],
            'longitude': s['geometry']['location']['lng'],
            'place_id': placeId
        }
        return data

    def geocode_place(self, ac):
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
            'placeId': ac['place_id'],
            'address': street + " " + street_number,
            'city': city,
            'state': state,
            'country': country,
            'zip_code': zip_code,
            'latitude': s['geometry']['location']['lat'],
            'longitude': s['geometry']['location']['lng']
        }

    def read(self, file_name):
        obj = self.s3_resource.Object(self.bucket_name, file_name)
        self.data = json.loads(obj.get()['Body'].read())
        return self.data

    def overwrite(self):
        self.s3_resource.Object(self.bucket_name, self.file_name).put(Body=json.dumps(self.data, sort_keys=True, indent=4), ACL='public-read')
        
        archive_version = self.get_archive_sequence()
        self.s3_resource.Object(self.bucket_name, 'archive/{}_{}'.format(str(archive_version), self.file_name)).put(Body=json.dumps(self.data, sort_keys=True, indent=4))
        
        with open('./data.json', 'w') as fh:
            fh.write(json.dumps(self.data, indent=4, sort_keys=True))

        return True

    def get_archive_sequence(self):
        paginator = self.s3_client.get_paginator('list_objects_v2')
        operation_parameters = {'Bucket': self.s3_bucket, 'Prefix': 'archive/'}
        page_iterator = paginator.paginate(**operation_parameters)
        versions = [int(f['Key'].lstrip('archive/').split('_')[0]) for page in page_iterator for f in page['Contents'] if int(f['Size'])]
        return max(versions) + 1

    def write_image_to_s3(self, file_name, img, **kwargs):
        return self.s3_resource.Object(self.bucket_name, file_name).put(Body=img, **kwargs)

    def print_city_options(self):
        cities = self.data['destinations']
        half = math.ceil(len(cities) / 2)

        for i in range(half):
            print("{0: <35}".format(str(i + 1) + ". " + cities[i]['city']), end='')
            if i + half + 1 <= len(cities):
                print("{0}".format(str(i + half + 1) + ". " + cities[i + half]['city']))
            else:
                print()

    def print_place_options(self, selected_city):
        places = self.data['destinations'][selected_city]['places']
        half = math.ceil(len(places) / 2)

        for i in range(half):
            print("{0: <35}".format(str(i + 1) + ". " + places[i]['name']), end='')
            if i + half + 1 <= len(places):
                print("{0}".format(str(i + half + 1) + ". " + places[i + half]['name']))
            else: 
                print()

    ###CLI Functions
    def menu(self):
        """
        Main menu from which the user can select a list of different functions

        Args:
            None

        Returns:
            None
        """
        u.cls()

        while self.run:
            print('Main Menu\n')

            print('0. To Exit')
            print('1. Enter a new city')
            print('2. Enter a new place')
            print('3. Add an album to a place')
            print('4. Edit a city')
            print('5. Edit a place')
            print('6. Delete a city')
            print('7. Delete a place')

            print()

            selection = input('Selection: ')

            selection = u.try_cast(selection, int) 
            assert selection != None
            assert 0 <= selection <= 7

            if selection == 0:
                self.run = False
            elif selection == 1:
                self.add_city()
            elif selection == 2:
                self.add_place()
            elif selection == 3:
                self.add_album()
            elif selection == 4:
                self.edit_city()
            elif selection == 5:
                self.edit_place()
            elif selection == 6:
                self.delete_city()
            elif selection == 7:
                self.delete_place()

    def add_city(self):
        """
        Adding a city to the dictionary

        Args:
            None

        Returns:
            None
        """

        u.cls()

        print('Enter city name to use the autocomplete functionality.')

        inp = input('Input: ')
        
        print()

        if inp == '\\':
            u.cls()
            return 0
        
        ac = m.get_city_suggestions(inp)
            
        if ac:
            s = [(i['description'], i['place_id']) for i in ac]

            print("0. Go Back")
            for x in range(len(s)): 
                print("{}. {}".format(x + 1, s[x][0]))

            print()
            sel = input('Selection (leave blank to go back): ')
            
            #Try to convert to int, if fails raise error
            sel = u.try_cast(sel, int) - 1
            assert sel != None
            #If the user selects 0, go back to the input screen
            if sel == -1:
                u.cls()
                self.add_city()
                return 0
            assert 0 <= sel <= len(s)
            
            selected_city = s[sel]

            #Check if the selected city is already in the dictionary
            assert selected_city[1] not in self.cities

            gc = self.geocode_city(selected_city[1])
            gc['places'] = []
            
            self.data['destinations'].append(gc)
            self.cities.append(gc['place_id'])

            u.cls()
        
        else:
            u.cls()

            print('City could not be found :(')
            print('Enter in the Place ID below (https://developers.google.com/maps/documentation/javascript/place-id)', '\n')

            inp = input('Place ID: ')
            if inp == '\\':
                u.cls() 
                return 0

            gc = self.geocode_city(inp)

            gc['places'] = []
            
            self.data['destinations'].append(gc)
            self.cities.append(gc['place_id'])

            u.cls()

        self.edit_city(len(self.cities) - 1)

    def delete_city(self):
        """
        Deleting a city from the dictionary

        Args:
            None

        Returns:
            None
        """

        u.cls()

        print('Select a city to delete')
        
        print()
        
        self.print_city_options()

        print()

        inp = input('Selection: ')

        if inp == '\\':
            u.cls()
            return

        selected_city = u.try_cast(inp, int) - 1
        assert selected_city != None
        assert 0 <= selected_city <= len(self.data['destinations'])

        #Delete the City from the dictionary
        del self.data['destinations'][selected_city]

        self.overwrite()

        u.cls()


    def edit_city(self, override_city=None):
        """
        Editing the information of a city in the dictionary

        Args:
            override_city::[int] 
                the ID of the city containing the place.  If not specified, the user will be prompted to select a city

        Returns:
            None
        """

        u.cls()

        if override_city == None:
            print('Select a city', '\n')
            
            self.print_city_options()

            print()

            inp = input('Selection: ')
            
            if inp == '\\':
                u.cls()
                return

            selected_city = u.try_cast(inp, int) - 1
            assert selected_city != None
            assert 0 < selected_city <= len(self.data['destinations'])
        else:
            selected_city = override_city

        # city = self.data['destinations'][selected_city]

        u.cls()

        #Iterate through all the attributes of the object and give the option to change the current values
        delete = []
        for k, v in self.data['destinations'][selected_city].items():
            if isinstance(v, (str, int, float)):
                #Populate the input with the existing value, so long as it is not a list or dict
                inp = u.rlinput('{}: '.format(k), str(v) if isinstance(v, (str, int, float)) else "")
                #try to cast the input as a float
                inp_as_float = u.try_cast(inp, float)
                #If the user types delete, add the attribute to the delete list
                if inp == 'delete':
                    delete.append(k)
                #If the input is a number, save it as a float or int
                elif inp_as_float != None:
                    self.data['destinations'][selected_city][k] = inp_as_float if '.' in inp else int(inp) 
                #if the input is a string, save it as such
                else:
                    self.data['destinations'][selected_city][k] = inp
        
        #becuase you can't delete from a dict while iterating over it, save the attributes you want to delete and then delete them
        for k in delete:
            del self.data['destinations'][selected_city][k]

        #overwrite the JSON file
        self.overwrite()

        u.cls()


    def add_place(self, override_city=None):
        """
        Adding a place to the dictionary

        Args:
            override_city::[int] 
                the ID of the city containing the place.  If not specified, the user will be prompted to select a city

        Returns:
            None
        """

        u.cls()
        
        if override_city == None: 
            print('Select a city')

            print()
            
            self.print_city_options()

            print()

            inp = input('Selection: ')

            if inp == '\\':
                u.cls()
                return 

            selected_city = u.try_cast(inp, int) - 1
            assert selected_city != None
            assert 0 <= selected_city <= len(self.data['destinations'])

            u.cls()

        else:
            selected_city = override_city

        city = self.data['destinations'][selected_city]

        print('Selected City: {}'.format(city['city']))
        print('Enter a place name to use the autocomplete functionality.')

        print()

        inp = input('Input: ')

        if inp == '\\':
            u.cls()
            return 

        #TODO pull this constant out
        sugs = self.get_place_suggestions(inp, location=[city['latitude'], city['longitude']], radius=25000)

        print()

        print('0. Go Back')
        for i, sug in enumerate(sugs):
            print("{}. {}".format(i + 1, sug['structured_formatting'].get('main_text', "") + " " + sug['structured_formatting'].get('secondary_text', "")))

        print()

        selection = input('Selection: ')

        if selection == '\\':
            u.cls()
            return 0

        selection = u.try_cast(selection, int) - 1
        assert selection != None
        if selection == -1:
            u.cls()
            self.add_place(selected_city)
            return
        assert 0 <= selection <= 4

        #Geocode the place and fill in some info
        place = self.geocode_place(ac=sugs[selection])

        if place['placeId'] not in self.places:
            place['main_type'] = ''
            place['city'] = city['city']
            place['images'] = []
            self.data['destinations'][selected_city]['places'].append(place) 

            #Allow user to edit autocomplete information
            self.edit_place(selected_city, len(self.data['destinations'][selected_city]['places']) - 1)
        
            search_albums = input('Search for albums? (y/n): ')

            u.cls()
            
            if search_albums.lower() == 'y':
                #Allow the user to link a GP album to the place
                self.add_album(selected_city, len(self.data['destinations'][selected_city]['places']) - 1, allow_add_another=False)

            add_another = input('Add Another? (y/n): ')

            u.cls()
            
            if add_another.lower() == 'y':
                self.add_place(override_city=selected_city)
        
        u.cls()


    def edit_place(self, override_city=None, override_place=None):
        """
        Editing the information of a place in the dictionary

        Args:
            override_city::[int] 
                the ID of the city containing the place.  If not specified, the user will be prompted to select a city

            override_place::[int]
                the ID of the place.  If not specified the user will be prompted to select a place
        Returns:
            None
        """

        u.cls()
        
        if override_city == None: 
            print('Select a city', '\n')
            
            self.print_city_options()

            print()

            inp = input('Selection: ')

            if inp == '\\':
                u.cls()
                return 0

            selected_city = u.try_cast(inp, int) - 1
            assert selected_city != None
            assert 0 < selected_city <= len(self.data['destinations'])
        else:
            selected_city = override_city

        city = self.data['destinations'][selected_city]

        u.cls()

        if override_place == None:
            print('Selected City: {}'.format(city['city']))

            print('Select a place to edit', '\n')

            self.print_place_options(selected_city)

            print()

            inp = input("Selection: ")

            if inp == '\\':
                u.cls()
                return 0

            selected_place = u.try_cast(inp, int) - 1
            assert selected_place != None
            if selected_place == -1:
                u.cls()
                self.edit_place(selected_city)
                return 0
        else:
            selected_place = override_place
        
        assert 0 <= selected_place < len(self.data['destinations'][selected_city]['places'])
        
        u.cls()

        #Iterate through all the attributes of the object and give the option to change the current values
        delete = []
        for k, v in self.data['destinations'][selected_city]['places'][selected_place].items():
            if isinstance(v, (str, int, float)):
                #Populate the input with the existing value, so long as it is not a list or dict
                inp = u.rlinput('{}: '.format(k), str(v) if isinstance(v, (str, int, float)) else "")
                #try to cast the input as a float
                inp_as_float = u.try_cast(inp, float)
                #If the user types delete, add the attribute to the delete list
                if inp == 'delete':
                    delete.append(k)
                #If the input is a number, save it as a float or int
                elif inp_as_float != None:
                    self.data['destinations'][selected_city]['places'][selected_place][k] = inp_as_float if '.' in inp else int(inp) 
                #if the input is a string, save it as such
                else:
                    self.data['destinations'][selected_city]['places'][selected_place][k] = inp
        
        #becuase you can't delete from a dict while iterating over it, save the attributes you want to delete and then delete them
        for k in delete:
            del self.data['destinations'][selected_city]['places'][selected_place][k]

        #overwrite the JSON file
        self.overwrite()

        u.cls()


    def delete_place(self, override_city=None):
        """
        Deleting a place from the dictionary

        Args:
            override_city::[int] 
                the id of the city containing the place.  If not specified, the user will be prompted to select a city

        Returns:
            None
        """

        u.cls()

        if override_city == None:
            print('Select a city', '\n')
            
            self.print_city_options()

            print()

            inp = input('Selection: ')

            if inp == '\\':
                u.cls()
                return

            selected_city = u.try_cast(inp, int) - 1
            assert selected_city != None
        else:
            assert isinstance(override_city, int)
            selected_city = override_city

        assert 0 < selected_city <= len(self.data['destinations'])

        u.cls()

        print('Select a place to delete', '\n')

        self.print_place_options(selected_city)

        print()

        inp = input('Selection: ')

        if inp == '\\':
            u.cls()
            return

        selected_place = u.try_cast(inp, int) - 1
        assert selected_place != None
        if inp == -1:
            u.cls()
            self.delete_place(selected_city)
            return 0
        assert 0 <= selected_place < len(self.data['destinations'][selected_city]['places'])
        
        del self.data['destinations'][selected_city]['places'][selected_place]

        self.overwrite()

        u.cls()


    def add_album(self, override_city=None, override_place=None, allow_add_another=True):
        """
        Download photos from a Google Photos album and add them to a place

        Args:
            override_city::[int] 
                the ID of the city containing the place.  If not specified, the user will be prompted to select a city

            override_place::[int]
                the ID of the place.  If not specified the user will be prompted to select a place

            allow_add_another::[bool]
                whether the user should be prompted to add another album to another place
        
        Returns:
            None
        """

        #Throw an error if override_city == None and override_place != None
        assert not (override_city == None and override_place != None)

        #Get City
        if override_city == None:     
            u.cls()

            print('Select a city', '\n')
            
            self.print_city_options()

            print()

            inp = input('Selection: ')

            if inp == '\\':
                u.cls()
                return

            selected_city = u.try_cast(inp, int) - 1
            assert selected_city != None
            assert 0 <= selected_city < len(self.data['destinations'])
            assert len(self.data['destinations'][selected_city]['places']) > 0
        
        else:
            selected_city = override_city

        u.cls()

        #Get Place
        if override_place == None:
            u.cls()

            print('Select a place', '\n')

            self.print_place_options(selected_city)

            print()

            sel = input('Selection: ')

            if sel == '\\':
                u.cls()
                return

            selected_place = u.try_cast(sel, int) - 1
            assert selected_place != None
            #If the user selects 0, go back
            if selected_place == -1:
                u.cls()
                self.add_album()
                return 0 
            assert 0 <= selected_place < len(self.data['destinations'][selected_city]['places'])

            

        else:
            assert isinstance(override_place, int)
            selected_place = override_place

        u.cls()

        if self.data['destinations'][selected_city]['places'][selected_place].get('albumId', None) != None:
            print("Album already exists for this place!")

        #Get album name
        album_name = input('Search for albums: ')

        if album_name == '\\':
            u.cls()
            return

        #Get suggestions from Google Photos, limit to 5
        suggestions = self.gp.get_album_suggestions(self.gp.get_albums(), album_name, 5)

        print()

        print("0. To Go Back")
        for i, suggestion in enumerate(suggestions):
            print('{}. {}'.format(i + 1, suggestion[0]))

        print()

        inp = input('Selection: ') 

        if inp == '\\':
            u.cls()
            return

        #Decrement by 1 since Python indexs at 0
        selection = u.try_cast(inp, int) - 1
        assert selection != None
        #If the user entered 0, go back
        if selection == -1:
            u.cls()
            self.add_album(override_city=selected_city, override_place=selected_place)
            return
        assert 0 <= selection < len(suggestions)
        

        #Otherwise get the photos from the selection
        photos = self.gp.get_album_photos(suggestions[selection][1])

        u.cls()

        #TODO: Should probably also clean out the directory in S3
        self.data['destinations'][selected_city]['places'][selected_place]['images'] = []
        self.data['destinations'][selected_city]['places'][selected_place]['albumId'] = suggestions[selection][1]

        #Retrieve the corresponding city and place objects
        city = self.data['destinations'][selected_city]['city']
        place = self.data['destinations'][selected_city]['places'][selected_place]['name']

        for i, photo in enumerate(photos):
            print("Uploading Image {} out of {}".format(i, len(photos)))
            
            r = requests.get(photo['baseUrl']+'=d')
            r.raw.decode_content = True # handle spurious Content-Encoding

            #Save the file contents to a variable
            content = r.content

            #Open the image in Pillow to get its height and width
            image = Image.open(io.BytesIO(content))
            width, height = image.size

            #Save the image back out to a buffer and repoint the buffer back to the beginning
            buffer = io.BytesIO()
            image.save(buffer, 'PNG')
            buffer.seek(0)

            #Hash the image content to generate a unique name, this will also help prevent duplicates
            md5 = hl.md5()
            md5.update(content)
            file_name = md5.hexdigest() + ".png"

            #Generate the S3 file path
            file_path = "{}/{}/{}/".format('images', city, place).replace(" ", "_")

            #Write the image to S3
            # self.s3_resource.Object(self.bucket_name, file_path + file_name).put(Body=buffer, ACL='public-read', ContentType='image/png')
            self.write_image_to_s3(file_path + file_name, buffer, ACL='public-read', ContentType='image/png')

            #Update the data to reflect the image upload
            self.data['destinations'][selected_city]['places'][selected_place]['imagesPath'] = self.s3_base + file_path
            self.data['destinations'][selected_city]['places'][selected_place]['images'].append({
                'src': self.s3_base + file_path + file_name,
                'width': width,
                'height': height,
                'hash': md5.hexdigest()
            })

            u.cls()

        self.overwrite()
        u.cls()

        if allow_add_another:
            add_another = input('Add Another? (y/n): ')

            u.cls()
            if add_another.lower() == 'y':
                self.add_album(override_city=selected_city)
                

if __name__ == '__main__':
    import configparser as cp

    config = cp.ConfigParser()
    config.read('config.ini')

    GOOGLE_PHOTOS_SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']
    GOOGLE_PHOTOS_CLIENT_SECRET_FILE = './google_client_secret.json'

    assert os.path.isfile(GOOGLE_PHOTOS_CLIENT_SECRET_FILE), "Google Photos Secret Can't be Found"

    gp = GooglePhotos(GOOGLE_PHOTOS_CLIENT_SECRET_FILE, GOOGLE_PHOTOS_SCOPES)

    m = Manager(config['AWS']['BUCKET'], config['AWS']['FILE_NAME'], gp)
    m.menu()