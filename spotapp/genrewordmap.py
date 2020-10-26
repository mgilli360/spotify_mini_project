# Created by: Mathieu Gilli
# Goal: Create routes for genre word map page

# Relevant modules/packages from package
from spotapp import app
from spotapp.classes import SpotifyUser

# Relevant modules/packages from pip
import matplotlib
matplotlib.use('Agg')
from flask import render_template, session
import requests
import json
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
from matplotlib import pyplot as plt
import os
from datetime import datetime
import pandas as pd

# Define genre wordmap route
@app.route("/hub/genrewordmap", methods=["GET","POST"])
def genrewordmap():
    # Instantiate a spotify user
    visit = SpotifyUser()
    #Get a new refreshed token
    refresh_token = visit.get_refresh_token(session["original_refresh_token"])

    # Get number of clusters from session (this is used to generate the nav items)
    try:
        cluster_num = session["cluster_number"]
    except:
        cluster_num = "NA"

    # Prepare request to get users saved tracks
    artists_to_query = []
    iteration = 1
    try:
        track_url = user_saved_tracks["next"]
    except:
        track_url = "https://api.spotify.com/v1/me/tracks?limit=50"

    # Update while loop here when we are ready to run code for everysong - without iteration block
    while track_url != None and iteration <= 20:
        try:
            r = visit.make_an_api_call(track_url, {"Authorization": "Bearer " + refresh_token})
            # Parse Response
            user_saved_tracks = json.loads(r.content)
            # Save artist url in list
            for i in user_saved_tracks["items"]:
                for i2 in i["track"]["artists"]:
                    for i3, i4 in i2.items():
                        if i3 == 'href':
                            artists_to_query.append(i4)
                            track_url = user_saved_tracks["next"]
        except:
            continue
        iteration += 1
    
    # Make a request to get users saved tracks related ARTIST
    genres = []
    for artist in artists_to_query:
        # Make api call to get artist data
        try:
            r = visit.make_an_api_call(artist, {"Authorization": "Bearer " + refresh_token})
            # Parse Response
            user_saved_artists = json.loads(r.content)
            # Add genres of queried song to list of genres to analyse
            for i in user_saved_artists.get("genres", "NA"):
                genres.append(i)
        except:
            continue

    # Generate wordmap
    # Update stopwords
    stopwords = set(STOPWORDS)
    stopwords.update(["NA"])

    # Convert list of genres into one big string of genres
    genres_string = " ".join(genres)

    # Create and generate a word cloud image
    wordcloud = WordCloud(stopwords=stopwords, background_color="white").generate(genres_string)

    # Display the generated image:
    plt.figure()
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")

    # Option 1: Display and save the generated image:
    datetimenow_format = str(datetime.utcnow()).replace(" ", "").replace(":", "").replace(".", "").replace("-", "")
    file_name = "wordmap" + str(datetimenow_format) + ".png"
    save_image_path = os.path.join("spotapp/static/genre_wordmap/",file_name)
    display_image_path = os.path.join("static/genre_wordmap/",file_name)
    wordcloud.to_file(save_image_path)
    plt.close("all")
    # Option 2: Would be not saving the image, instead pass it as bytes to the template. Need research to complete

    # Generate table with count of genres
    df_genres = pd.DataFrame(genres, columns = ["genre"])
    genres_count = df_genres.genre.value_counts().to_frame("count")
    
    # Generate the table sum
    genres_count_sum = genres_count["count"].sum()
    
    # Transform into dictionary to pass to the template
    genres_count_dic = genres_count.to_dict("index")

    # Return template for that user
    return render_template("genrewordmap.html", display_image_path=display_image_path, genres_count_dic=genres_count_dic, genres_count_sum=genres_count_sum, cluster_num=cluster_num)
    