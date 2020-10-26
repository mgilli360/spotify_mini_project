# Created by: Mathieu Gilli
# Goal: Create DB models for app

# Relevant modules/packages from package
from spotapp import db

# Create DB model for Users Table
class Users(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(255), index = True, unique = True)
    created_on = db.Column(db.String(50), index = True, unique = False)

# Create DB model(s) table(s)
db.create_all()