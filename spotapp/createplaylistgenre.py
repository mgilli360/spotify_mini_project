# Created by: Mathieu Gilli
# Goal: Create playlist in spotify for genres of music

# Relevant modules/packages from package
from spotapp import app
from spotapp.classes import SpotifyUser

# Relevant modules/packages from pip
from flask import redirect, session, url_for
import pandas as pd
import math
import urllib.parse

# Define track genre route for creating playlists
@app.route("/hub/genrewordmap/<string:genre>", methods=["GET","POST"])
def createplaylistgenre(genre):    
    # Instantiate a spotify user
    visit = SpotifyUser()
    #Get a new refreshed token
    refresh_token = visit.get_refresh_token(session["original_refresh_token"])

    # Get results from session
    genres_uri = session["genres_uri"]
    df_genres = pd.DataFrame(genres_uri, columns=["uri", "genre"])
        
    ## Add column with url encoded genre value
    df_genres["genre_url"] = df_genres["genre"].apply(lambda x : urllib.parse.quote(x)).astype(str)
    
    # Filter on Genre Selected
    df_genres = df_genres[df_genres.genre == str(genre)]

    # Create playlist for Genre
    h = {"Content-Type":"application/json", "Authorization":"Bearer " + str(refresh_token)}
    playlist_id = visit.create_playlist(h, session["user_id"], "Genre: " + str(urllib.parse.unquote(genre)))
    
    # Get songs URIs
    df_genres_uri_list = df_genres.uri.unique().tolist()

    # Add song to newly created playlist
    run_count = math.ceil(len(df_genres_uri_list) / 50)
    i = 0
    for run in range(run_count):
        temp_uri_list = []
        while len(temp_uri_list) <= 50:
            try:
                temp_uri_list.append(df_genres_uri_list[i])
                i += 1
            except:
                break
        result = visit.add_song_playlist(h, playlist_id, temp_uri_list)
        print(result)

    return redirect(url_for("genrewordmap", _external=True))
