import configparser as cp
import json
import boto3
import pickle
import os
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

from fuzzywuzzy import fuzz


SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']
CLIENT_SECRET_FILE = '/home/michael/Downloads/client_secret_533824499350-pb7pa1qg5m7mvf5jnin0t0t1sdruesos.apps.googleusercontent.com.json'

class GooglePhotos(object):
    def __init__(self, client_secret_file, scopes):
        self.service = self.Create_Service(CLIENT_SECRET_FILE, 'photoslibrary', 'v1', SCOPES)
        self.albums = self.get_albums()


    def Create_Service(self, client_secret_file, api_name, api_version, *scopes):
        API_SERVICE_NAME = api_name
        API_VERSION = api_version

        cred = None

        pickle_file = f'token_{API_SERVICE_NAME}_{API_VERSION}.pickle'
        if os.path.exists(pickle_file):
            with open(pickle_file, 'rb') as token:
                cred = pickle.load(token)

        if not cred or not cred.valid:
            if cred and cred.expired and cred.refresh_token:
                cred.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CLIENT_SECRET_FILE, SCOPES)
                cred = flow.run_local_server()

            with open(pickle_file, 'wb') as token:
                pickle.dump(cred, token)

        try:
            service = build(API_SERVICE_NAME, API_VERSION, credentials=cred)
            return service
        except Exception as e:
            print(e)

    def get_albums(self):
        a = []

        pageToken = ''
        loop = True
        while loop:
            albums = self.service.albums().list(pageSize=50, pageToken=pageToken).execute()
            for album in albums['albums']:
                a.append(album)

            pageToken = albums.get('nextPageToken', '')
            if pageToken == '':
                loop = False

        return a

    def get_album_id(self, album_name):
        for album in self.albums:
            if album_name == album['title']:
                return album['id']

    def get_album_info(self, album_id):
        return self.service.albums().get(albumId=album_id).execute()

    def get_album_photos(self, album_id):
        photos = []

        page_token = ''
        loop = True 
        while loop:
            resp = self.service.mediaItems().search(body={'albumId': album_id, 'pageToken': page_token, 'pageSize': 50}).execute()
            photos += resp['mediaItems']

            page_token = resp.get('nextPageToken', '')
            if page_token == '':
                loop = False
        
        return photos

    def get_album_suggestions(self, albums, entry, n=5):
        albums = [(i['title'], i['id']) for i in albums]

        def fuzzy_match_rating(a):
            return -fuzz.token_set_ratio(entry.lower(), a[0].lower())

        return sorted(albums, key=fuzzy_match_rating)[:n]

    
if __name__ == '__main__':
    service = GooglePhotos(CLIENT_SECRET_FILE, SCOPES)
    