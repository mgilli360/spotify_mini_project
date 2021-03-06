# Created by: Mathieu Gilli
# Goal: Create playlist in spotify for clusters

# Relevant modules/packages from package
from spotapp import app
from spotapp.classes import SpotifyUser

# Relevant modules/packages from pip
from flask import redirect, session, url_for
import pandas as pd
import math

# Define track cluster route for creating playlists
@app.route("/hub/trackcluster/result/<int:num>", methods=["GET","POST"])
def createplaylistcluster(num):
    # Instantiate a spotify user
    visit = SpotifyUser()
    #Get a new refreshed token
    refresh_token = visit.get_refresh_token(session["original_refresh_token"])

    # Get results from session
    cluster_result_dic = session["cluster_result"]
    cluster_result = pd.DataFrame(cluster_result_dic)
    ## add 1 to cluster
    cluster_result = cluster_result.copy()
    cluster_result.cluster = cluster_result.cluster + 1
    # Filter on Cluster Selected
    cluster_result = cluster_result[cluster_result.cluster == num]

    # Get describe table results from session
    cluster_result_describe_dic = session["cluster_describe_result"]
    cluster_result_describe = pd.DataFrame(cluster_result_describe_dic)
    # Filter on Cluster Selected
    cluster_result_describe = cluster_result_describe[cluster_result_describe.cluster == num]
    cluster_result_describe = cluster_result_describe[cluster_result_describe.stat == "mean"]
    # Convert to index dic
    cluster_result_describe = cluster_result_describe.to_dict("index")
    # Print output into sentence
    output = "Cluster results -> | "
    for values in cluster_result_describe.values():
        for key, value in values.items():
            output += str(key) + ": " + str(value) + " | " 

    # Create playlist for cluster
    h = {"Content-Type":"application/json", "Authorization":"Bearer " + str(refresh_token)}
    playlist_id = visit.create_playlist(h, session["user_id"], "Cluster " + str(num), str(output))
    
    # Get songs URIs
    cluster_uri_list = cluster_result.uri.unique().tolist()

    # Add song to newly created playlist
    run_count = math.ceil(len(cluster_uri_list) / 50)
    i = 0
    for run in range(run_count):
        temp_uri_list = []
        while len(temp_uri_list) <= 50:
            try:
                temp_uri_list.append(cluster_uri_list[i])
                i += 1
            except:
                break
        result = visit.add_song_playlist(h, playlist_id, temp_uri_list)
        print(result)

    return redirect(url_for("trackclusterresult", _external=True))
