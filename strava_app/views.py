from datetime import datetime
from flask import Flask, render_template
from . import app
import requests
import urllib3
import json
import os
from .get_data import get_access_token, get_activity_ids, get_activity_data, get_activity_laps


@app.route("/")
def home():
    # data = get_dataset()

    access_token = get_access_token()
    activity_ids = get_activity_ids(access_token)
    df = get_activity_data(access_token, activity_ids)
    # activity_laps = get_activity_laps(access_token, activity_ids)
    
    column_names = ['ID', 
                    'Date', 
                    'Time', 
                    'Name', 
                    'Distance', 
                    'Run Time', 
                    'Type', 
                    'Pace', 
                    'Average Heart Rate', 
                    'Average Cadence',
                    'Effort (1-10)', 
                    'Notes', 
                    'Map']

    # link_column is the column that adds a button. Hyperlink would look nicer than button
    # return render_template("home.html", column_names=df.columns.values, row_data=list(df.values.tolist()), link_column="Map", zip=zip)
    return render_template("home.html", column_names=column_names, row_data=list(df.values.tolist()), link_column="Map", zip=zip)


@app.route("/about/")
def about():
    return render_template("about.html")

@app.route("/api/")
def api():
    # my_dataset = get_dataset()

    return render_template("api.html")

# @app.route("/api/data")
# def get_data():

#     return app.send_static_file("data.json")
