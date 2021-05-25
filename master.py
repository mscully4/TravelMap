import configparser as cp
import os
import argparse

# from utils.constants import TABLE_NAMES, TABLE_KEYS
import os 
from constants import TABLE_NAMES, TABLE_KEYS
from Objects.Destination import Destination
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
import asyncio

import utils

def upload_cover_photo(destination_id, place_id, album_id, **kwargs):
    album = Album(destination_id, place_id, album_id, **gp.get_album_info(album_id))
    cover_photo = Photo(photo_id=album.cover_photo_id, place_id=place_id, destination_id=destination_id)
    cover_photo.download(url=album.cover_photo_download_url, is_cover_image=True)
    album.cover_photo_src = cover_photo.write(s3)
    albums_table.insert(album)

def upload_photos(photos_table, album_id, destination_id, place_id):
    photos = gp.get_album_photos(album_id)
    l = []
    if photos:
        for i, obj in enumerate(photos):
            # utils.cls()
            print(f"{i} out of {len(photos)} photos uploaded")
            photo = Photo(destination_id=destination_id, place_id=place_id, **obj)
            photo.download(obj.get('baseUrl'))
            photo.write(s3)
            l.append(photo.serialize())
    
    obj = {
        "destination_id": destination_id,
        "place_id": place_id,
        "photos": l
        }

    photos_table.insert(obj)

async def main(args):
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

    destinations_table = Table(
        create_dynamo_table_client(db, TABLE_NAMES.DESTINATIONS), 
        partition_key=TABLE_KEYS.DESTINATIONS.PARTITION_KEY
    )
    places_table = Table(
        create_dynamo_table_client(db, TABLE_NAMES.PLACES), 
        partition_key=TABLE_KEYS.PLACES.PARTITION_KEY, 
        sort_key=TABLE_KEYS.PLACES.SORT_KEY
    )
    albums_table = Table(
        create_dynamo_table_client(db, TABLE_NAMES.ALBUMS), 
        partition_key=TABLE_KEYS.ALBUMS.PARTITION_KEY, 
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
        print('1. Enter a new destination')
        print('2. Enter a new place')
        print('3. Add an album to a place')
        print('4. Edit a destination')
        print('5. Edit a place')
        print('6. Delete a destination')
        print('7. Delete a place')
        print('8. Upload Photos')
        print('9. Upload Album Cover')

        print()

        selection = input('Selection: ')

        selection = utils.try_cast(selection, int) 
        assert selection != None
        assert 0 <= selection <= 9

        utils.cls()
        if selection == 0:
            #Exit
            run = False
        elif selection == 1:
            #Add City
            place_id = CLI.add_destination(gm)
            data = gm.geocode_destination(place_id)
            if data['destination_id'] not in destinations_table.get_keys():
                destinations_table.insert(Destination(**data))
            else:
                print("City already exists")
        elif selection == 2:
            #Add Place to City
            destinations = destinations_table.get()
            destination = Destination(**destinations[CLI.select_destination(destinations)])
            data = CLI.add_place(gm, destination)
            data['destination_id'] = destination.destination_id
            data['city'] = destination.name
            if data['place_id'] not in places_table.get_keys():
                places_table.insert(Place(**data))
            else:
                print("Place already exists")

        elif selection == 3:
            #Add Album to Place
            destinations = destinations_table.get()
            destination = Destination(**destinations[CLI.select_destination(destinations)])

            places = places_table.get(partition_key_value=destination.destination_id)
            place = Place(**places[CLI.select_place(places)])

            try:
                album = Album(**albums_table.get(partition_key_value=destination.destination_id, sort_key_value=place.place_id)[0])
            except:
                album = None
            
            if not album or CLI.override_album() == False:
                album = Album(destination_id=destination.destination_id, place_id=place.place_id, **CLI.add_album(gp, destination, place))
                cover_photo = Photo(photo_id=album.cover_photo_id, place_id=place.place_id, destination_id=destination.destination_id)
                cover_photo.download(url=album.cover_photo_download_url, is_cover_image=True)
                album.cover_photo_src = cover_photo.write(s3)
                albums_table.insert(album)

            if CLI.ask_true_false_question("Would you like to upload photos? (y/n): "):
                upload_photos(photos_table, album.album_id, destination.destination_id, place.place_id)
            # photos = gp.get_album_photos(album.album_id)
            # if photos:
            #     for i, obj in enumerate(photos):
            #         # utils.cls()
            #         print(f"{i} out of {len(photos)} photos uploaded")
            #         photo = Photo(destination_id=destination.destination_id, place_id=place.place_id, **obj)
            #         photo.download(obj.get('baseUrl'))
            #         photo.write(s3)
            #         photos_table.insert(photo)

        elif selection == 4:
            #Edit City
            destinations = destinations_table.get()
            destination = Destination(**destinations[CLI.select_destination(destinations)])
            CLI.edit_destination(destination)
            destinations_table.update(destination)
        elif selection == 5:
            #Edit Place
            destinations = destinations_table.get()
            destination = Destination(**destinations[CLI.select_destination(destinations)])
            places = places_table.get(partition_key_value=destination.destination_id)
            place = Place(**places[CLI.select_place(places)])
            CLI.edit_place(place)
            places_table.update(place)
        elif selection == 6:
            #Delete a City
            destinations = destinations_table.get()
            destination = Destination(**destinations[CLI.select_destination(destinations)])
            destinations_table.delete(destination)
        elif selection == 7:
            #Delete a Place
            destinations = destinations_table.get()
            destination = Destination(**destinations[CLI.select_destination(destinations)])
            places = places_table.get(partition_key_value=destination.destination_id)
            place = Place(**places[CLI.select_place(places)])
            places_table.delete(place)
        elif selection == 8:
            destinations = destinations_table.get()
            sel = CLI.select_destination(destinations)
            if sel == "*":
                pass
            else:
                destination = Destination(**destinations[sel])

                places = places_table.get(partition_key_value=destination.destination_id)
                sel = CLI.select_place(places)

                if sel == "*":
                    pass
                else:
                    place = Place(**places[sel])

                    album = Album(**albums_table.get(partition_key_value=destination.destination_id, sort_key_value=place.place_id))
                    photos = gp.get_album_photos(album.album_id)
                    if photos:
                        for i, obj in enumerate(photos):
                            # utils.cls()
                            print(f"{i} out of {len(photos)} photos uploaded")
                            photo = Photo(destination_id=destination.destination_id, place_id=place.place_id, **obj)
                            photo.download(obj.get('baseUrl'))
                            photo.write(s3)
                            photos_table.insert(photo)

        elif selection == 9:
            destinations = destinations_table.get()
            sel = CLI.select_destination(destinations)
            if sel == "*":
                albums = albums_table.get()
                for i, album in enumerate(albums):
                    print(f"{i} out of {len(albums)} cover photos uploaded")
                    upload_cover_photo(**album)
            else:
                destination = Destination(**destinations[sel])
                places = places_table.get(partition_key_value=destination.destination_id)
                sel = CLI.select_place(places)
                if sel == "*":
                    albums = albums_table.get(partition_key_value=destination.destination_id)
                    for i, album in enumerate(albums):
                        print(f"{i} out of {len(albums)} cover photos uploaded")
                        upload_cover_photo(**album)
                else:
                    place = Place(**places[sel])
                    album = albums_table.get(partition_key_value=destination.destination_id, sort_key_value=place.place_id)
                    upload_cover_photo(**album)

            
        #     places = places_table.get(partition_key_value=destination.place_id)
        #     place = Place(**places[CLI.select_place(places)])

        #     album = Album(**albums_table.get(partition_key_value=destination.place_id, sort_key_value=place.place_id)[0])
        #     gp.get_album_info(album.album_id)
            # CLI.upload_cover_photo(gp, destination, place)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config-file', required=True, type=str, help="The path to the config file")
    parser.add_argument('-p', '--google-photos-secret', required=True, type=str, help="The path to the Google Photos Secret file")

    args = vars(parser.parse_args())
    asyncio.get_event_loop().run_until_complete(main(args))
