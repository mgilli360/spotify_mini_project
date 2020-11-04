# Created by: Mathieu Gilli
# Goal: Create routes for genre word map page

# Relevant modules/packages from package
from spotapp import app, celery, s3, s3_client
from spotapp.classes import SpotifyUser

# Relevant modules/packages from pip
import matplotlib
matplotlib.use('Agg')
from flask import render_template, session, redirect, url_for
import requests
import json
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
from matplotlib import pyplot as plt
import os
from datetime import datetime
import pandas as pd
import urllib.parse

# Create celery task to generate the wordmap
@celery.task(name="create_wordmap")
def create_wordmap(refresh_token, n):
    # Instantiate a spotify user
    visit = SpotifyUser()

    # Prepare request to get users saved tracks
    artists_to_query = []
    iteration = 1
    try:
        track_url = user_saved_tracks["next"]
    except:
        track_url = "https://api.spotify.com/v1/me/tracks?limit=50"

    # Update while loop here when we are ready to run code for everysong - without iteration block
    while track_url != None and iteration <= (n / 50):
        try:
            r = visit.make_an_api_call(track_url, {"Authorization": "Bearer " + refresh_token})
            # Parse Response
            user_saved_tracks = json.loads(r.content)
            # Save artist url in list
            for i in user_saved_tracks["items"]:
                song_uri = i["track"]["uri"]
                for i2 in i["track"]["artists"]:
                    for i3, i4 in i2.items():
                        if i3 == 'href':
                            artists_to_query.append([song_uri, i4])
                            track_url = user_saved_tracks["next"]
        except:
            continue
        iteration += 1
    
    # Make a request to get users saved tracks related ARTIST
    genres_uri = []
    genres = []
    for song_uri, artist in artists_to_query:
        # Make api call to get artist data
        try:
            r = visit.make_an_api_call(artist, {"Authorization": "Bearer " + refresh_token})
            # Parse Response
            user_saved_artists = json.loads(r.content)
            # Add genres of queried song to list of genres to analyse
            for i in user_saved_artists.get("genres", "NA"):
                genres_uri.append([song_uri, i])
                genres.append(i)
        except:
            continue
    
    # Generate wordmap, first Update stopwords:
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

    # Upload a new file (send image to S3)
    data = open(save_image_path, "rb")
    s3.Bucket("spotify-mini-project-assets").put_object(Key=save_image_path, Body=data)

    # Generate table with count of genres
    df_genres = pd.DataFrame(genres, columns = ["genre"])
    genres_count = df_genres.genre.value_counts().to_frame("count")
    genres_count = genres_count.reset_index() 
    genres_count.columns = ["genre", "count"]
    genres_count["genre_url"] = genres_count["genre"].apply(lambda x : urllib.parse.quote(x)).astype(str)
    
    # Transform into dictionary to pass to the template
    genres_count_dic = genres_count.to_dict("index")

    # Generate the table sum
    genres_count_sum = genres_count["count"].count()

    # Prepare task result
    result = {
        "display_image_path": display_image_path,
        "save_image_path": save_image_path,
        "genres_count_dic": genres_count_dic,
        "genres_count_sum": int(genres_count_sum),
        "genres_uri": genres_uri
    }
    result_json = json.dumps(result)
    
    return result_json

# Define genre wordmap CREATION route
@app.route("/hub/genrewordmap/create", methods=["GET","POST"])
def genrewordmapcreate():
    # Remove celery task inside session
    session.pop("celery_task_genre_id", None)

    # Check if a new default nb_songs_query is set, if so use it. Else use the default of 1000
    try:
        n = session["nb_songs_query"]
    except:
        n = 1000

    # Instantiate a spotify user
    visit = SpotifyUser()
    # Get a new refreshed token
    refresh_token = visit.get_refresh_token(session["original_refresh_token"])

    # Start celery task to create wordmap
    res = create_wordmap.delay(refresh_token, n)
    # Store celery task inside session
    session["celery_task_genre_id"] = res.id

    # Return template for that user
    return redirect(url_for("genrewordmap", _external=True))

# Define genre wordmap route
@app.route("/hub/genrewordmap", methods=["GET","POST"])
def genrewordmap():
    # Get number of clusters from session (this is used to generate the nav items)
    try:
        cluster_num = session["cluster_number"]
    except:
        cluster_num = "NA"
    # Get celery_task_cluster_id of cluster from session (this is used to generate the nav items)
    try:
        celery_task_cluster_id = session["celery_task_cluster_id"]
    except:
        celery_task_cluster_id = "NA"
    # Check if a new default nb_songs_query is set, if so use it. Else use the default of 1000
    try:
        n = session["nb_songs_query"]
    except:
        n = 1000

    # celery_task_genre_id from session
    task_id = session["celery_task_genre_id"]
    # Get genres_count_sum, genres_count_dic and display_image_path of wordmap from celery_task
    try:
        # Getting the celery_task results
        res = celery.AsyncResult(task_id)

        # Getting the celery_task status, if True: set the session + variables to tasks results
        if res.ready():
            # Set function variables
            result_json = json.loads(res.get())
            display_image_path = result_json["display_image_path"]
            genres_count_dic = result_json["genres_count_dic"]
            genres_count_sum = result_json["genres_count_sum"]
            genres_uri = result_json["genres_uri"]
            save_image_path = result_json["save_image_path"]
            # Clear session variables
            session.pop("display_image_path", None)
            session.pop("genres_count_dic", None)
            session.pop("genres_count_sum", None)
            session.pop("genres_uri", None)
            session.pop("save_image_path", None)
            # Set session variables
            session["display_image_path"] = display_image_path
            session["genres_count_dic"] = genres_count_dic
            session["genres_count_sum"] = genres_count_sum
            session["genres_uri"] = list(genres_uri)
            session["save_image_path"] = save_image_path

            # Download new results from S3
            s3_client.download_file("spotify-mini-project-assets", save_image_path, save_image_path)
        # If new task was started
        elif res.status == "STARTED":
            display_image_path = "NA"
            genres_count_dic = "NA"
            genres_count_sum = "NA"
            genres_uri = "NA"
            save_image_path = "NA"
        # If unsuccessful use session
        else: 
            display_image_path = session["display_image_path"]
            genres_count_dic = session["genres_count_dic"]
            genres_count_sum = session["genres_count_sum"]
            genres_uri = session["genres_uri"]    
            save_image_path = session["save_image_path"]

            # Download new results from S3
            s3_client.download_file("spotify-mini-project-assets", save_image_path, save_image_path)
    # If unsuccessful set the variables to "NA"
    except:
        display_image_path = "NA"
        genres_count_dic = "NA"
        genres_count_sum = "NA"
        genres_uri = "NA"
        save_image_path = "NA"

    # Return template for that user
    return render_template("genrewordmap.html", cluster_num=cluster_num, display_image_path=display_image_path, genres_count_dic=genres_count_dic,\
        genres_count_sum=genres_count_sum, n=n, celery_task_cluster_id=celery_task_cluster_id)