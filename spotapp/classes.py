# Created by: Mathieu Gilli
# Goal: Create class models for app

# Relevant modules/packages from pip
import requests
import json
import uuid
import os

class SpotifyUser:
    # Spotify attributes that are constant for every user
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    response_type = "code"
    redirect_uri = "http%3A%2F%2F127.0.0.1%3A5000%2Fhub" #Hint: https://www.urlencoder.org/
    state = str(uuid.uuid4().hex)
    scope = "user-library-read user-read-email playlist-modify-private playlist-modify-public"
    show_dialog = False
    auth = f"https://accounts.spotify.com/authorize?client_id={client_id}&response_type={response_type}&redirect_uri={redirect_uri}&state={state}&scope={scope}&show_dialog={show_dialog}"
    client_id_and_secret = os.environ.get("SPOTIFY_CLIENT_SECRET_KEY") # Base64URL format
    header = {"Authorization": f"Basic {client_id_and_secret}"}

    # Method to get first auth token
    def get_first_token(self, auth_code):
        # Request variables
        payload = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": "http://127.0.0.1:5000/hub"
        }
        # Make request to get first token
        token = requests.post("https://accounts.spotify.com/api/token", data=payload, headers=self.header)
        # Parse request content
        token_exchange_response = json.loads(token.content)
        # Return the refresh_token
        return token_exchange_response["refresh_token"]

    # Method to get refresh auth token
    def get_refresh_token(self, token):
        # Request variables
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": token
        }
        # Make request to get refresh token
        token = requests.post("https://accounts.spotify.com/api/token", data=payload, headers=self.header)
        # Parse request content
        token_exchange_response = json.loads(token.content)
        # Return the access_token
        return token_exchange_response["access_token"]

    # Method to make api calls
    def make_an_api_call(self, url, h):
        r = requests.get(url, headers=h)
        return r
    
    # Method to get refresh auth token
    def create_playlist(self, h, user_id, name):
        # Request variables
        payload = {
            "name": name,
            "public": False,
            "description": "Playlist created from Spotify Mini App - Enjoy!"
        }
        # Make request to get refresh token
        token = requests.post(url="https://api.spotify.com/v1/users/" + str(user_id) + "/playlists", data=json.dumps(payload), headers=h)
        # Parse request content
        token_exchange_response = json.loads(token.content)
        
        # Return the access_token
        return token_exchange_response["id"]

    # Method to get refresh auth token
    def add_song_playlist(self, h, playlist_id, uri):
        # Request variables
        payload = {
            "uris": uri
        }
        # Make request to get refresh token
        token = requests.post(url="https://api.spotify.com/v1/playlists/" + str(playlist_id) + "/tracks", data=json.dumps(payload), headers=h)
        # Parse request content
        token_exchange_response = json.loads(token.content)
        
        # Return the access_token
        return token_exchange_response
        