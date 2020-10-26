# Created by: Mathieu Gilli
# Goal: Create routes for showing clusters results

# Relevant modules/packages from package
from spotapp import app
from spotapp.classes import SpotifyUser

# Relevant modules/packages from pip
from flask import render_template, request, session
import json
import pandas as pd
from sklearn.cluster import KMeans
import numpy as np

# Define track cluster route
@app.route("/hub/trackcluster/result", methods=["GET","POST"])
def trackclusterresult():
    # Instantiate a spotify user
    visit = SpotifyUser()
    #Get a new refreshed token
    refresh_token = visit.get_refresh_token(session["original_refresh_token"])
    # Get number of clusters from session
    cluster_num = session["cluster_number"]
    # Get results from session
    cluster_result_dic = session["cluster_result"]
    cluster_result = pd.DataFrame(cluster_result_dic)

    # Return results to html - change order
    cluster_result_html = cluster_result[["cluster", "name", "acousticness", "danceability", "energy", "instrumentalness", "liveness", "loudness", "mode", "speechiness", "tempo", "valence"]]
    ## add 1 to cluster
    cluster_result_html = cluster_result_html.copy()
    cluster_result_html.cluster = cluster_result_html.cluster + 1
    ## save column names
    cluster_result_html_columns = cluster_result_html.columns.values.tolist()   
    ## cluster_result_html table column formatted
    cluster_result_html_format = pd.DataFrame()
    for column in cluster_result_html_columns:
        cluster_result_html_format[column] = cluster_result_html[column].apply(lambda x: str("{:.2f}".format(round(x, 2))).rstrip('0').rstrip('.') if isinstance(x, float) else x)
    ## convert to dic
    cluster_result_dic = cluster_result_html_format.to_dict("index")

    # Describe table after clustering
    model_columns = ["acousticness", "danceability", "energy", "instrumentalness", "liveness", "loudness", "mode", "speechiness", "tempo", "valence"]
    unique_clusters = cluster_result_html.cluster.unique().tolist()
    unique_clusters.sort()
    describe_table = pd.DataFrame()
    for cluster in unique_clusters:
        temp_describe_table = pd.DataFrame()
        cluster_df = cluster_result_html[cluster_result_html.cluster == cluster]
        for column in model_columns:
            temp_describe_table["cluster"] = cluster
            temp_describe_table[column] = cluster_df[column].describe().round(decimals=2).apply(lambda x: str("{:.2f}".format(round(x, 2))).rstrip('0').rstrip('.'))
        describe_table = describe_table.append(temp_describe_table)
    
    #Render pandas descriptive table to html for webpage
    ## convert to dic
    describe_table = describe_table.reset_index()    
    describe_table.columns = ["","cluster", "acousticness", "danceability", "energy", "instrumentalness", "liveness", "loudness", "mode", "speechiness", "tempo", "valence"]
    describe_table_dic_html = describe_table.to_dict("index")
    ## save column names
    describe_table_columns = describe_table.columns.values.tolist()
    
    # Return template for that user
    return render_template("trackclusterresult.html", cluster_result_dic=cluster_result_dic, cluster_num=cluster_num, cluster_result_html_columns=cluster_result_html_columns,\
        describe_table_columns=describe_table_columns, describe_table_dic_html=describe_table_dic_html)