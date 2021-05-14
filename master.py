import configparser as cp
import os
import argparse

# from utils.constants import TABLE_NAMES, TABLE_KEYS
import os 
print(os.getcwd())
from constants import *
from Objects.City import City
from Objects.Place import Place
from Objects.Album import Album
from Objects.Photo import Photo
from Objects.Table import Table
from GoogleMaps import GoogleMaps
from GooglePhotos import GooglePhotos
from DynamoDB import create_dynamo_resource, create_dynamo_table_client
import DynamoDB as ddb
import CLI
from S3 import S3

import utils

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config-file', required=True, type=str, help="The path to the config file")
    parser.add_argument('-p', '--google-photos-secret', required=True, type=str, help="The path to the Google Photos Secret file")

    args = vars(parser.parse_args())
    
    #Retrieving keys from config file
    assert os.path.exists(args['config_file'])
    config = cp.ConfigParser()
    config.read(args['config_file'])

    #Instantiating Google Photos class
    GOOGLE_PHOTOS_SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']
    assert os.path.isfile(args['google_photos_secret'])
    gp = GooglePhotos(args['google_photos_secret'], GOOGLE_PHOTOS_SCOPES)
    
    #Instantiating Google Maps class
    assert config['GOOGLE'].get('API_KEY', False)
    gm = GoogleMaps(api_key=config['GOOGLE'].get('API_KEY'))

    s3 = S3(config['S3'].get('BUCKET'), config['S3'].get('REGION'))

    db = create_dynamo_resource()

    cities_table = Table(
        create_dynamo_table_client(db, TABLE_NAMES.CITIES), 
        partition_key=TABLE_KEYS.CITIES.PARTITION_KEY
    )
    places_table = Table(
        create_dynamo_table_client(db, TABLE_NAMES.PLACES), 
        partition_key=TABLE_KEYS.PLACES.PARTITION_KEY, 
        sort_key=TABLE_KEYS.PLACES.SORT_KEY
    )
    album_table = Table(
        create_dynamo_table_client(db, TABLE_NAMES.ALBUMS), 
        partition_key=TABLE_KEYS.PLACES.PARTITION_KEY, 
        sort_key=TABLE_KEYS.ALBUMS.SORT_KEY
    )
    photos_table = Table(
        create_dynamo_table_client(db, TABLE_NAMES.PHOTOS), 
        partition_key=TABLE_KEYS.PHOTOS.PARTITION_KEY, 
        sort_key=TABLE_KEYS.PHOTOS.SORT_KEY
    )


    run = True
    while run:
        # utils.cls()
        print('Main Menu\n')

        print('0. To Exit')
        print('1. Enter a new city')
        print('2. Enter a new place')
        print('3. Add an album to a place')
        print('4. Edit a city')
        print('5. Edit a place')
        print('6. Delete a city')
        print('7. Delete a place')
        print('8. Upload Photos')
        print('9. Upload Album Cover')

        print()

        selection = input('Selection: ')

        selection = utils.try_cast(selection, int) 
        assert selection != None
        assert 0 <= selection <= 9

        if selection == 0:
            #Exit
            run = False
        elif selection == 1:
            #Add City
            place_id = CLI.add_city(gm)
            data = gm.geocode_city(place_id)
            if data['place_id'] not in cities_table.get_keys():
                cities_table.insert(City(**data))
            else:
                print("City already exists")
        elif selection == 2:
            #Add Place to City
            cities = cities_table.get()
            data = CLI.add_place(gm, cities)
            if data['place_id'] not in places_table.get_keys():
                places_table.insert(Place(**data))
            else:
                print("Place already exists")

        elif selection == 3:
            #Add Album to Place
            cities = cities_table.get()
            city = City(**cities[CLI.select_city(cities)])

            places = places_table.get(partition_key_value=city.place_id)
            place = Place(**places[CLI.select_place(places)])

            album = Album(**CLI.add_album(gp, city, place))
            album_table.insert(album)
            photos = gp.get_album_photos(album.album_id)
            if photos:
                for p in photos:
                    p['city_id'] = city.place_id
                    p['place_id'] = place.place_id
                    photo = Photo(**p)
                    photo.write(s3)
                    photos_table.insert(photo)

        elif selection == 4:
            #Edit City
            cities = cities_table.get()
            city = City(**cities[CLI.select_city(cities)])
            CLI.edit_city(city)
            cities_table.update(city)
        elif selection == 5:
            #Edit Place
            cities = cities_table.get()
            city = City(**cities[CLI.select_city(cities)])
            places = places_table.get(partition_key_value=city.place_id)
            place = Place(**places[CLI.select_place(places)])
            CLI.edit_place(place)
            places_table.update(place)
        elif selection == 6:
            #Delete a City
            cities = cities_table.get()
            city = City(**cities[CLI.select_city(cities)])
            cities_table.delete(city)
        elif selection == 7:
            #Delete a Place
            cities = cities_table.get()
            city = City(**cities[CLI.select_city(cities)])
            places = places_table.get(partition_key_value=city.place_id)
            place = Place(**places[CLI.select_place(places)])
            places_table.delete(place)
        # elif selection == 8:
        #     self.upload_photos()
        # elif selection == 9:
        #     self.upload_cover_photo()
