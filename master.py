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
from pyfiglet import Figlet

import utils

APP_NAME = 'Travel Map CLI'

class TravelMapCLI(object):
    def __init__(self):
        self.gp = None
        self.gm = None
        self.s3 = None
        self.dynamo = None

        self.destinations_table = None
        self.places_table = None
        self.albums_table = None

        self._run = False

    def set_gp(self, gp):
        assert isinstance(gp, GooglePhotos)
        self.gp = gp

    def set_gm(self, gm):
        self.gm = gm

    def set_s3(self, s3):
        assert isinstance(s3, S3)
        self.s3 = s3

    def set_dynamo(self, dynamo):
        self.dynamo = dynamo
        self._create_table_clients()

    def _create_table_clients(self):
        assert self.dynamo, "Dynamo Client does not exist yet :("
        self.destinations_table = Table(
            create_dynamo_table_client(self.dynamo, TABLE_NAMES.DESTINATIONS),
            Destination,
            partition_key=TABLE_KEYS.DESTINATIONS.PARTITION_KEY
        )

        self.places_table = Table(
            create_dynamo_table_client(self.dynamo, TABLE_NAMES.PLACES),
            Place,
            partition_key=TABLE_KEYS.PLACES.PARTITION_KEY,
            sort_key=TABLE_KEYS.PLACES.SORT_KEY
        )

        self.albums_table = Table(
            create_dynamo_table_client(self.dynamo, TABLE_NAMES.ALBUMS),
            Album,
            partition_key=TABLE_KEYS.ALBUMS.PARTITION_KEY,
            sort_key=TABLE_KEYS.ALBUMS.SORT_KEY
        )

        self.photos_table = Table(
            create_dynamo_table_client(self.dynamo, TABLE_NAMES.PHOTOS),
            Photo,
            partition_key=TABLE_KEYS.PHOTOS.PARTITION_KEY,
            sort_key=TABLE_KEYS.PHOTOS.SORT_KEY
        )

    async def run(self):
        self._run = True

        while (self._run):
            CLI.print_menu()
            sel = CLI.get_selection(0, 9)

            if sel == 0:
                self._run = False
                if not self.gp.done:
                    self.gp.albums.cancel()
            elif sel == 1:
                self.add_destination()
            elif sel == 2:
                self.add_place()
            elif sel == 3:
                await self.add_album()
            elif sel == 4:
                self.edit_destination()
            elif sel == 5:
                self.edit_place()
            elif sel == 6:
                self.delete_destination()
            elif sel == 7:
                self.delete_place()
            elif sel == 8:
                self.add_photos()
            elif sel == 9:
                self.add_cover_photo()

    def _select_destination(self):
        destinations = self.destinations_table.get()
        CLI.print_double_list(destinations)
        sel = CLI.get_selection(0, len(destinations)) - 1
        CLI.print_figlet(APP_NAME)
        return destinations[sel]

    def _select_place(self, destination):
        places = self.places_table.get(partition_key_value=destination.destination_id)
        CLI.print_double_list(places)
        sel = CLI.get_selection(0, len(places)) - 1
        CLI.print_figlet(APP_NAME)
        return places[sel] if isinstance(sel, int) else sel

    
    def _upload_photos(self, destination_id, place_id):
        album = self.albums_table.get(partition_key_value=destination_id, sort_key_value=place_id)[0]
        photos = self.gp.get_album_photos(album.album_id)
        if photos:
            downloaded_photos = []
            for i, obj in enumerate(photos):
                print(f"{i} out of {len(photos)} photos uploaded")
                photo = Photo(destination_id=destination_id, place_id=place_id, **obj)
                photo.download(obj.get('baseUrl'))
                photo.write(self.s3)
                downloaded_photos.append(photo.serialize())
                utils.clr_line()

            self.photos_table.insert({
                TABLE_KEYS.PHOTOS.PARTITION_KEY: destination_id,
                TABLE_KEYS.PHOTOS.SORT_KEY: place_id,
                "photos": downloaded_photos
            })

    def _upload_cover_photo(self, album):
        cover_photo = Photo(photo_id=album.cover_photo_id, place_id=album.place_id, destination_id=album.destination_id)
        cover_photo.download(url=album.cover_photo_download_url, is_cover_image=True)
        album.cover_photo_src = cover_photo.write(self.s3)
        self.albums_table.insert(album)

    def add_destination(self):
        CLI.print_figlet(APP_NAME)

        #Add Destination
        inp = CLI.get_input('Enter destination name to use the autocomplete functionality.')
        if inp == '\\':
            utils.cls()
            return

        suggestions = self.gm.get_destination_suggestions(inp)
        if suggestions:
            CLI.print_figlet(APP_NAME)
            CLI.print_single_list([suggestion['description'] for suggestion in suggestions])
            sel = CLI.get_selection(0, len(suggestions)) - 1

            if sel == -1:
                self.add_destination()
                return

            id_ = suggestions[sel]['place_id']
        
        else:
            CLI.print_figlet(APP_NAME)

            print('City could not be found :(')
            print('Enter in the Place ID below (https://developers.google.com/maps/documentation/javascript/place-id)', '\n')

            id_ = input('Place ID: ')
            if inp == '\\':
                utils.cls() 
                return 0
        
        data = self.gm.geocode_destination(id_)
        destination = Destination(**data)

        if destination.destination_id not in self.destinations_table.get_keys():
            self.destinations_table.insert(destination)


    def add_place(self, destination=None):
        CLI.print_figlet(APP_NAME)

        #Add Place to Destinations
        if not destination:
            destination = self._select_destination()

        CLI.print_figlet(APP_NAME)
        print('Selected Destination: {}'.format(destination.name))
        print()
        inp = CLI.get_input('Enter a place name to use the autocomplete functionality.')
        if inp == '\\':
            utils.cls()
            return

        suggestions = self.gm.get_place_suggestions(inp, location=[destination.latitude, destination.longitude])

        CLI.print_single_list(
            [f"{sug['structured_formatting'].get('main_text', '')} {sug['structured_formatting'].get('secondary_text', '')}" for sug in suggestions]
        )
        sel = CLI.get_selection(0, len(suggestions)) - 1

        if sel == -1:
            self.add_place(destination=destination)
            return

        data = self.gm.geocode_place(suggestions[sel]['place_id'])
        place = Place(**data, name=suggestions[sel]['structured_formatting']['main_text'], destination_id=destination.destination_id, city=destination.name)
        if place.place_id not in self.places_table.get_keys():
            self.places_table.insert(place)

    async def add_album(self, destination=None):
        #Add Album to Place
        # assert isinstance(destination, (None, Destination))
        if not destination:
            destination = self._select_destination()

        place = self._select_place(destination)

        try:
            album = self.albums_table.get(partition_key_value=destination.destination_id, sort_key_value=place.place_id)[0]
        except:
            album = None

        if not album or CLI.ask_yes_no_question("An album already exists for this place.  Overwrite? (y/n): "):
            inp = CLI.get_input('Enter the album name to use the autocomplete functionality.', f"{destination.name} -- {place.name}")

            if inp == '\\':
                utils.cls()
                return

            if not self.gp.done:
                await self.gp.albums
            
            suggestions = self.gp.get_album_suggestions(self.gp.albums.result(), inp, 5)
            # There should just be a function called print_suggestion_list
            CLI.print_single_list([sug[0] for sug in suggestions])
            sel = CLI.get_selection(0, len(suggestions)) - 1
            data = self.gp.get_album_info(suggestions[sel][1])
            album = Album(destination_id=destination.destination_id, place_id=place.place_id, **data)
            self._upload_cover_photo(album)
            self.albums_table.insert(album)

        # if CLI.ask_yes_no_question("Would you like to upload photos? (y/n): "):
        #     photos = gp.get_album_photos(album.album_id)
        #     upload_photos(photos, photos_table, album.album_id, destination.destination_id, place.place_id)

    def edit_destination(self, destination=None):
        CLI.print_figlet(APP_NAME)
        if not destination:
            destination = self._select_destination()

        destination = CLI.edit_obj(destination)
        self.destinations_table.update(destination)

    def edit_place(self, destination=None, place=None):
        CLI.print_figlet(APP_NAME)
        if not destination:
            destination = self._select_destination()

        if not place:
            place = self._select_place(destination)

        place = CLI.edit_obj(place)
        self.places_table.update(place)

    def delete_destination(self):
        CLI.print_figlet(APP_NAME)
        destination = self._select_destination()
        self.destinations_table.delete(destination)

    def delete_place(self):
        CLI.print_figlet(APP_NAME)
        destination = self._select_destination()
        place = self._select_place(destination)
        self.places_table.delete(place)

    def add_photos(self, destination=None, place=None):
        CLI.print_figlet(APP_NAME)
        if not destination:
            destination = self._select_destination()

        if not place:
            #Don't use self._select_place to prevent having to do another call to get all places later
            places = self.places_table.get(partition_key_value=destination.destination_id)
            CLI.print_double_list(places)
            sel = CLI.get_selection(0, len(places))
            place = places[sel - 1] if isinstance(sel, int) else sel

        if sel == "*":
            for place in places:
                print(f"Downloading Photos of {place.name}")
                self._upload_photos(destination.destination_id, place.place_id)
        else:
            self._upload_photos(destination.destination_id, place.place_id)

    def add_cover_photo(self, destination=None):
        '''
        This needs to be updated to pull a fresh download url
        '''
        assert destination == None or isinstance(destination, Destination)
        CLI.print_figlet(APP_NAME)

        if not destination:
            destination = self._select_destination()

        place = self._select_place(destination)
        
        if place == "*":
            albums = self.albums_table.get(partition_key_value=destination.destination_id)
            for i, album in enumerate(albums):
                print(f"{i} out of {len(albums)} cover photos uploaded")
                data = self.gp.get_album_info(album.album_id)
                album.cover_photo_download_url = data.get('coverPhotoBaseUrl', "")
                self._upload_cover_photo(album)
                self.albums_table.insert(album)
        else:
            album = self.albums_table.get(partition_key_value=destination.destination_id, sort_key_value=place.place_id)[0]
            data = self.gp.get_album_info(album.album_id)
            album.cover_photo_download_url = data.get('coverPhotoBaseUrl', "")
            self._upload_cover_photo(album)
            self.albums_table.insert(album)


async def main(args):
    # Retrieving keys from config file
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

    cli = TravelMapCLI()
    cli.set_gm(gm)
    cli.set_gp(gp)
    cli.set_s3(s3)
    cli.set_dynamo(db)
    await cli.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config-file', required=True, type=str, help="The path to the config file")
    parser.add_argument('-p', '--google-photos-secret', required=True, type=str, help="The path to the Google Photos Secret file")

    args = vars(parser.parse_args())
    asyncio.get_event_loop().run_until_complete(main(args))

    # # Retrieving keys from config file
    # assert os.path.exists(args['config_file'])
    # config = cp.ConfigParser()
    # config.read(args['config_file'])

    # #Instantiating Google Photos class
    # GOOGLE_PHOTOS_SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']
    # assert os.path.isfile(args['google_photos_secret'])
    # gp = GooglePhotos(args['google_photos_secret'], GOOGLE_PHOTOS_SCOPES)
    
    # #Instantiating Google Maps class
    # assert config['GOOGLE'].get('API_KEY', False)
    # gm = GoogleMaps(api_key=config['GOOGLE'].get('API_KEY'))

    # s3 = S3(config['S3'].get('BUCKET'), config['S3'].get('REGION'))

    # db = create_dynamo_resource()

    # cli = TravelMapCLI()
    # cli.set_gm(gm)
    # cli.set_gp(gp)
    # cli.set_s3(s3)
    # cli.set_dynamo(db)
    # asyncio.get_event_loop().run_until_complete(cli.run())

#     asyncio.get_event_loop().run_until_complete(main(args))

# def add_destination(destinations_table, gm):
#     #Add Destination
#     place_id = CLI.add_destination(gm)
#     destination = Destination(**gm.geocode_destination(place_id))
#     if destination.destination_id not in destinations_table.get_keys():
#         destinations_table.insert(destination)
#     else:
#         print("City already exists")

# def add_place(destinations_table, places_table, gm):
#     #Add Place to City
#     destinations = destinations_table.get()
#     destination = Destination(**destinations[CLI.select_destination(destinations)])
#     data = gm.geocode_place(CLI.add_place(gm, destination))
#     data['destination_id'] = destination.destination_id
#     data['city'] = destination.name
#     if data['place_id'] not in places_table.get_keys():
#         places_table.insert(Place(**data))
#     else:
#         print("Place already exists")

# def upload_cover_photo(albums_table, s3, destination_id, place_id, album_id, **kwargs):
#     album = Album(destination_id, place_id, album_id, **gp.get_album_info(album_id))
#     cover_photo = Photo(photo_id=album.cover_photo_id, place_id=place_id, destination_id=destination_id)
#     cover_photo.download(url=album.cover_photo_download_url, is_cover_image=True)
#     album.cover_photo_src = cover_photo.write(s3)
#     albums_table.insert(album)

# def upload_photos(photos, photos_table, s3, destination_id, place_id):
#     if photos:
#         downloaded_photos = []
#         for i, obj in enumerate(photos):
#             print(f"{i} out of {len(photos)} photos uploaded")
#             photo = Photo(destination_id=destination_id, place_id=place_id, **obj)
#             photo.download(obj.get('baseUrl'))
#             photo.write(s3)
#             downloaded_photos.append(photo.serialize())
#             utils.clr_line()

#         photos_table.insert({
#             TABLE_KEYS.PHOTOS.PARTITION_KEY: destination_id,
#             TABLE_KEYS.PHOTOS.SORT_KEY: place_id,
#             "photos": downloaded_photos
#         })


# async def main(args):
#     #Retrieving keys from config file
#     assert os.path.exists(args['config_file'])
#     config = cp.ConfigParser()
#     config.read(args['config_file'])

#     #Instantiating Google Photos class
#     GOOGLE_PHOTOS_SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']
#     assert os.path.isfile(args['google_photos_secret'])
#     gp = GooglePhotos(args['google_photos_secret'], GOOGLE_PHOTOS_SCOPES)
    
#     #Instantiating Google Maps class
#     assert config['GOOGLE'].get('API_KEY', False)
#     gm = GoogleMaps(api_key=config['GOOGLE'].get('API_KEY'))

#     s3 = S3(config['S3'].get('BUCKET'), config['S3'].get('REGION'))

#     db = create_dynamo_resource()

#     destinations_table = Table(
#         create_dynamo_table_client(db, TABLE_NAMES.DESTINATIONS), 
#         partition_key=TABLE_KEYS.DESTINATIONS.PARTITION_KEY
#     )
#     places_table = Table(
#         create_dynamo_table_client(db, TABLE_NAMES.PLACES), 
#         partition_key=TABLE_KEYS.PLACES.PARTITION_KEY, 
#         sort_key=TABLE_KEYS.PLACES.SORT_KEY
#     )
#     albums_table = Table(
#         create_dynamo_table_client(db, TABLE_NAMES.ALBUMS), 
#         partition_key=TABLE_KEYS.ALBUMS.PARTITION_KEY, 
#         sort_key=TABLE_KEYS.ALBUMS.SORT_KEY
#     )
#     photos_table = Table(
#         create_dynamo_table_client(db, TABLE_NAMES.PHOTOS), 
#         partition_key=TABLE_KEYS.PHOTOS.PARTITION_KEY, 
#         sort_key=TABLE_KEYS.PHOTOS.SORT_KEY
#     )

#     # state: [run, action, destination_override, place_override]
#     state = [True, 0, None, None]
#     while state[0]:
#         #If there is no action selected
#         if not state[1]:
#             utils.cls()
#             print(Figlet(font='slant').renderText(APP_NAME))
#             print('Main Menu')

#             print('0. To Exit')
#             print('1. Enter a new destination')
#             print('2. Enter a new place')
#             print('3. Add an album to a place')
#             print('4. Edit a destination')
#             print('5. Edit a place')
#             print('6. Delete a destination')
#             print('7. Delete a place')
#             print('8. Upload Photos')
#             print('9. Upload Album Cover')

#             print()

#             selection = input('Selection: ')

#             selection = utils.try_cast(selection, int) 
#             assert selection != None
#             assert 0 <= selection <= 9

#             state[1] = selection

#         utils.cls()
#         if state[1] == 0:
#             #Exit
#             state[0] = False
#         elif state[1] == 1:
#             #Add Destination
#             add_destination(gm, destinations_table)

#             if not CLI.ask_true_false_question("Would you like to add another destination? (y/n): "):
#                 state[1] = 0

#         elif state[1] == 2:
#             #Add Place to Destination
#             if state[2] == None:
#                 destinations = destinations_table.get()
#                 destination = Destination(**destinations[CLI.select_destination(destinations)])
#             else:
#                 destination = destinations_table.get(partition_key_value=state[2])

#             place_id = CLI.add_place(gm, destination)
#             if place_id not in places_table.get_keys():
#                 place = Place(**gm.geocode_place(place_id), destination_id=destination.destination_id, city=destination.name)
#                 places_table.insert(place)
#             else:
#                 print("Place already exists")

#             if CLI.ask_true_false_question("Would you like to add another destination? (y/n): "):
#                 state = [True, 2, None, None]
#             else:
#                 state = [True, None, None, None]


#         elif state[1] == 3:
#             #Add Album to Place
#             destinations = destinations_table.get()
#             destination = Destination(**destinations[CLI.select_destination(destinations)])

#             places = places_table.get(partition_key_value=destination.destination_id)
#             place = Place(**places[CLI.select_place(places)])

#             try:
#                 album = Album(**albums_table.get(partition_key_value=destination.destination_id, sort_key_value=place.place_id)[0])
#             except:
#                 album = None
            
#             if not album or CLI.override_album() == False:
#                 album = Album(destination_id=destination.destination_id, place_id=place.place_id, **CLI.add_album(gp, destination, place))
#                 cover_photo = Photo(photo_id=album.cover_photo_id, place_id=place.place_id, destination_id=destination.destination_id)
#                 cover_photo.download(url=album.cover_photo_download_url, is_cover_image=True)
#                 album.cover_photo_src = cover_photo.write(s3)
#                 albums_table.insert(album)

#             if CLI.ask_true_false_question("Would you like to upload photos? (y/n): "):
#                 photos = gp.get_album_photos(album.album_id)
#                 upload_photos(photos, photos_table, album.album_id, destination.destination_id, place.place_id)

#         elif state[1] == 4:
#             #Edit City
#             destinations = destinations_table.get()
#             destination = Destination(**destinations[CLI.select_destination(destinations)])
#             CLI.edit_destination(destination)
#             destinations_table.update(destination)
#         elif state[1] == 5:
#             #Edit Place
#             destinations = destinations_table.get()
#             destination = Destination(**destinations[CLI.select_destination(destinations)])
#             places = places_table.get(partition_key_value=destination.destination_id)
#             place = Place(**places[CLI.select_place(places)])
#             CLI.edit_place(place)
#             places_table.update(place)
#         elif state[1] == 6:
#             #Delete a Destination
#             destinations = destinations_table.get()
#             destination = Destination(**destinations[CLI.select_destination(destinations)])
#             destinations_table.delete(destination)

#             if CLI.ask_true_false_question("Would you like to delete another destination? (y/n): "):
#                 state = [True, 6, None, None]
#             else:
#                 state = [True, None, None, None]

#         elif state[1] == 7:
#             #Delete a Place
#             destinations = destinations_table.get()
#             destination = Destination(**destinations[CLI.select_destination(destinations)])
#             places = places_table.get(partition_key_value=destination.destination_id)
#             place = Place(**places[CLI.select_place(places)])
#             places_table.delete(place)
#         elif state[1] == 8:
#             destinations = destinations_table.get()
#             sel = CLI.select_destination(destinations)
#             if sel == "*":
#                 pass
#             else:
#                 destination = Destination(**destinations[sel])

#                 places = places_table.get(partition_key_value=destination.destination_id)
#                 sel = CLI.select_place(places)

#                 if sel == "*":
#                     for place in places:
#                         place = Place(**place)
#                         print(f"Downloading Photos of {place.name}")

#                         album = Album(**albums_table.get(partition_key_value=destination.destination_id, sort_key_value=place.place_id))
#                         photos = gp.get_album_photos(album.album_id)
#                         upload_photos(photos, photos_table, s3, destination.destination_id, place.place_id)

#                 else:
#                     place = Place(**places[sel])
#                     album = Album(**albums_table.get(partition_key_value=destination.destination_id, sort_key_value=place.place_id))
#                     photos = gp.get_album_photos(album.album_id)
#                     upload_photos(photos, photos_table, s3, destination.destination_id, place.place_id)

#         elif state[1] == 9:
#             destinations = destinations_table.get()
#             sel = CLI.select_destination(destinations)
#             if sel == "*":
#                 albums = albums_table.get()
#                 for i, album in enumerate(albums):
#                     print(f"{i} out of {len(albums)} cover photos uploaded")
#                     upload_cover_photo(**album)
#             else:
#                 destination = Destination(**destinations[sel])
#                 places = places_table.get(partition_key_value=destination.destination_id)
#                 sel = CLI.select_place(places)
#                 if sel == "*":
#                     albums = albums_table.get(partition_key_value=destination.destination_id)
#                     for i, album in enumerate(albums):
#                         print(f"{i} out of {len(albums)} cover photos uploaded")
#                         upload_cover_photo(**album)
#                 else:
#                     place = Place(**places[sel])
#                     album = albums_table.get(partition_key_value=destination.destination_id, sort_key_value=place.place_id)
#                     upload_cover_photo(**album)

            
# if __name__ == '__main__':
#     parser = argparse.ArgumentParser()
#     parser.add_argument('-c', '--config-file', required=True, type=str, help="The path to the config file")
#     parser.add_argument('-p', '--google-photos-secret', required=True, type=str, help="The path to the Google Photos Secret file")

#     args = vars(parser.parse_args())
#     asyncio.get_event_loop().run_until_complete(main(args))
