# Created by: Mathieu Gilli
# Goal: Create routes for home and hub pages

# Relevant modules/packages from package
from spotapp import app, db, session
from spotapp.db import users
from spotapp.classes import SpotifyUser

# Relevant modules/packages from pip
from flask import render_template, request
import json
from datetime import datetime

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

# Define successful connection route (the route after connecting the app with spotify)
@app.route("/hub", methods=["GET"])
def hub():
    # Instantiate a spotify user
    visit = SpotifyUser()  
    # Get number of clusters from session (this is used to generate the nav items)
    try:
        cluster_num = session["cluster_number"]
    except:
        cluster_num = "NA"
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

    # Return template for that user
    return render_template("hub.html", user_email=user_email, returning_user=returning_user, cluster_num=cluster_num)
    