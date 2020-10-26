# Created by: Mathieu Gilli
# Goal: Create routes for generating clusters

# Relevant modules/packages from package
from spotapp import app
from spotapp.classes import SpotifyUser

# Relevant modules/packages from pip
import matplotlib
matplotlib.use('Agg')
from flask import render_template, session, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired
import json
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import os
from datetime import datetime

# Define flask form to select K
num_clusters = list(range(2, 21))
class KSelectForm(FlaskForm):
    k = SelectField("Number of clusters to generate:", choices=num_clusters, validators=[DataRequired()])
    submit = SubmitField("Generate clusters")

# Define track cluster route
@app.route("/hub/trackcluster", methods=["GET","POST"])
def trackcluster():
    # First instantiate the form
    k_form = KSelectForm()
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
    song_to_query = []
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
                song_id = i["track"]["id"]
                song_name = i["track"]["name"]
                song_to_query.append([song_id, song_name])
                track_url = user_saved_tracks["next"]
        except:
            continue
        iteration += 1
        
    # Get Get Audio Features for Tracks queried
    audio_features = pd.DataFrame()
    for id, name in song_to_query:
        try:
            r = visit.make_an_api_call("https://api.spotify.com/v1/audio-features/" + id, {"Authorization": "Bearer " + refresh_token})
            # Parse Response
            audio_analysis = json.loads(r.content)
            # Add song_name to result
            audio_analysis["name"] = name
            # Update audio_features dataframe
            audio_features = audio_features.append(audio_analysis, ignore_index=True)
        except:
            continue
    
    # Pandas manipulations
    # Remove unwanted columns
    audio_features = audio_features.drop(["analysis_url", "duration_ms", "track_href", "type", "key"], axis=1)
    # Make sure there are no NA in table
    audio_features = audio_features.dropna()

    # Rearrange columns for html
    audio_features_html = audio_features[["name", "acousticness", "danceability", "energy", "instrumentalness", "liveness", "loudness", "mode", "speechiness", "tempo", "valence"]]
    # audio_features_html table column Names
    audio_features_html_columns = audio_features_html.columns.values.tolist()
    # audio_features_html table column formatted
    audio_features_html_format = pd.DataFrame()
    for column in audio_features_html_columns:
        audio_features_html_format[column] = audio_features[column].apply(lambda x: str("{:.2f}".format(round(x, 2))).rstrip('0').rstrip('.') if isinstance(x, float) else x)
    # Transform audio_features_html table into dictionary to pass to the template
    audio_features_html_format_dic = audio_features_html_format.to_dict("index")
    
    # Describe table clustering
    model_columns = ["acousticness", "danceability", "energy", "instrumentalness", "liveness", "loudness", "mode", "speechiness", "tempo", "valence"]
    describe_table = pd.DataFrame()
    for column in model_columns:
        describe_table[column] = audio_features[column].describe().round(decimals=2).apply(lambda x: str("{:.2f}".format(round(x, 2))).rstrip('0').rstrip('.'))
    # Descriptive table column Names
    describe_table_columns = describe_table.columns.values.tolist()
    # Transform descriptive table into dictionary to pass to the template
    describe_table_dic = describe_table.to_dict("index")

    # Normalize the table before clustering
    normalized_table = pd.DataFrame()
    for column in model_columns:
        normalized_table[column] = audio_features[column].apply(lambda x: (x - audio_features[column].mean()) / audio_features[column].std())

    # Generate graph to help user select best K for KMeans algorithm
    inertias = []
    for k in num_clusters:
        model = KMeans(n_clusters=k)
        model.fit(normalized_table)
        inertias.append(model.inertia_)
    # Generate graph
    plt.figure()
    ax = plt.subplot()
    plt.plot(num_clusters, inertias, "-o")
    plt.xlabel("Number of Clusters (k)")
    plt.ylabel("Inertia")
    plt.title("What is the optimal number of clusters?")
    ax.set_xticks(num_clusters)
    # Save graph
    datetimenow_format = str(datetime.utcnow()).replace(" ", "").replace(":", "").replace(".", "").replace("-", "")
    file_name = "kcluster" + str(datetimenow_format) + ".png"
    save_image_path = os.path.join("spotapp/static/k_cluster/",file_name)
    display_image_path = os.path.join("static/k_cluster/",file_name) 
    plt.savefig(save_image_path)
    plt.close("all")

    # Generate the clustering with K specified by user
    if k_form.validate_on_submit():
        # Clear the session result  
        session.pop("cluster_result", None)
        session.pop("cluster_number", None)
        # Get k from form
        k = k_form.k.data
        # Run model
        model = KMeans(n_clusters=int(k))
        model.fit(normalized_table)
        labels = model.predict(normalized_table)
        # Save results to session
        audio_features["cluster"] = labels
        audio_features_dic = audio_features.to_dict("list")
        session["cluster_result"] = audio_features_dic
        session["cluster_number"] = int(k)
        # Redirect to cluster result
        return redirect(url_for("trackclusterresult", _external=True))

    # Return template for that user
    return render_template("trackcluster.html", audio_features_html_columns=audio_features_html_columns, audio_features_html_format_dic=audio_features_html_format_dic, \
        display_image_path=display_image_path, template_form=KSelectForm(), describe_table_columns=describe_table_columns, describe_table_dic=describe_table_dic, \
        cluster_num=cluster_num)