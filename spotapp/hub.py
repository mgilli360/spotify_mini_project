# Created by: Mathieu Gilli
# Goal: Create routes for home and hub pages

# Relevant modules/packages from package
from spotapp import app, db
from spotapp.db import users
from spotapp.classes import SpotifyUser

# Relevant modules/packages from pip
from flask import render_template, request, redirect, url_for, session
import json
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired

# Define index route (the default route for the app)
@app.route("/", methods=["GET"])
def index():
    # Instantiate a spotify user
    visit = SpotifyUser()
    # Clear token in session
    session.pop("original_refresh_token", None)
    # Store state for verifications purposes
    session.pop("state", None)
    session["state"] = visit.state
    # Return template for that user
    return render_template("index.html", auth=visit.auth)

# Define flask form to select nb of tracks to process
num_tracks = list(range(50, 1001, 50))
class NTracks(FlaskForm):
    n = SelectField("Max number of songs to use in algorithm:", choices=num_tracks, validators=[DataRequired()], default=1000)
    submit = SubmitField("Update")

# Define successful connection route (the route after connecting the app with spotify)
@app.route("/hub", methods=["GET","POST"])
def hub(): 
    # Check if a new default nb_songs_query is set, if so use it. Else use the default of 1000
    try:
        n = session["nb_songs_query"]
        n_form = NTracks(n=n)
    except:
        n = 1000
        n_form = NTracks(n=1000)
    
    # Instantiate a spotify user
    visit = SpotifyUser() 

    # Get number of clusters from session (this is used to generate the nav items)
    try:
        cluster_num = session["cluster_number"]
    except:
        cluster_num = "NA"
    # Get celery_task_genre_id of wordmap from session (this is used to generate the nav items)
    try:
        celery_task_genre_id = session["celery_task_genre_id"]
    except:
        celery_task_genre_id = "NA"
    
    # OAuth flow
    try:
        # Get connection code arguments
        code = request.args.get("code", default=None)
        # Generate auth token for this code
        token = visit.get_first_token(code)
        # Get connection state arguments
        state = request.args.get("state", default=None)
        # Make sure the state is the same as the one set in the visit class
        if state == session["state"]:
            # Store token in session
            session["original_refresh_token"] = token
            # Get a new refreshed token
            refresh_token = visit.get_refresh_token(token)
        else:
            return "Error state invalid"
    except:
        #Get a new refreshed token
        refresh_token = visit.get_refresh_token(session["original_refresh_token"])

    # Display username on hub - get user email
    r = visit.make_an_api_call("https://api.spotify.com/v1/me", {"Authorization": "Bearer " + refresh_token})
    user_details = json.loads(r.content)
    user_email = user_details["email"]

    # Clear user id in session
    session.pop("user_id", None)
    # Clear user id in session
    session["user_id"] = user_details["id"]

    # Check if the user is already in the DB
    try:
        query_email = users.query.filter(users.email == user_email).first().email
    except:
        query_email = "NA"

    # If the user is not already in the DB, create the record
    if query_email == user_email:
        returning_user = True
    else:
        returning_user = False
        datetimenow_format = str(datetime.utcnow()).replace(" ", "-").replace(":", "-").replace(".", "-")
        db.session.add(users(email = user_email, created_on = str(datetimenow_format)))
        db.session.commit()
    
    # Form processing for changing the default number of songs to query
    if n_form.validate_on_submit():
        # Clear the session result  
        session.pop("nb_songs_query", None)
        # Get n from form
        n = n_form.n.data
        print(n)
        # Save results to session
        session["nb_songs_query"] = int(n)
        print(session["nb_songs_query"])
        # Redirect to cluster result
        return redirect(url_for("hub", _external=True))

    # Return template for that user
    return render_template("hub.html", user_email=user_email, returning_user=returning_user, cluster_num=cluster_num, celery_task_genre_id=celery_task_genre_id,\
        template_form=n_form, n=n)