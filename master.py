import configparser as cp
import os
import argparse

from Objects.City import City
from Objects.Place import Place
from GoogleMaps import GoogleMaps
from GooglePhotos import GooglePhotos
from DynamoDB import DynamoDB
from DynamoDB import metadata_get, metadata_add, metadata_remove
from DynamoDB import city_get, city_add
import DynamoDB as ddb
import CLI
# from CLI import add_city, edit_city, delete_city, add_place, edit_place, delete_place

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

    db = DynamoDB()
    metadata_table = db.create_dynamo_table_client('metadata')
    cities_table = db.create_dynamo_table_client('cities')
    places_table = db.create_dynamo_table_client('places')
    # metadata_add(metadata_table, "cities", "jdalfsdj")
    # metadata_remove(metadata_table, 'jdalfsdj')

    utils.cls()

    run = True
    while run:
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
            run = False
        elif selection == 1:
            #Add City
            place_id = CLI.add_city(gm)
            data = gm.geocode_city(place_id)
            print(data)
            if not data['place_id'] in metadata_get(metadata_table, "cities"):
                city = City(**data)
                metadata_add(metadata_table, 'cities', city.place_id)
                city_add(cities_table, city.serialize())
            else:
                print("City already exists")
        elif selection == 2:
            cities = city_get(cities_table)
            data = CLI.add_place(gm, cities)
            if data['place_id'] not in [x for x in metadata_get(metadata_table, 'places')]:
                place = Place(**data)
                metadata_add(metadata_table, 'places', place.place_id)
                city_add(places_table, place.serialize())

        elif selection == 3:
            cities = city_get(cities_table)
            selected_city = CLI.select_city(cities)
            # print(cities[selected_city]['place_id'])
            places = ddb.place_get(places_table, city_id=cities[selected_city]['place_id'])
            CLI.select_place(places)
            # CLI.add_album(cities, places)
        # elif selection == 4:
        #     self.edit_city()
        # elif selection == 5:
        #     self.edit_place()
        # elif selection == 6:
        #     self.delete_city()
        # elif selection == 7:
        #     self.delete_place()
        # elif selection == 8:
        #     self.upload_photos()
        # elif selection == 9:
        #     self.upload_cover_photo()
