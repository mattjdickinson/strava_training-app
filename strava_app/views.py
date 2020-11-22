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
    
    # link_column is the column that adds a button. Want this to be 'Show map'
    return render_template("home.html", column_names=df.columns.values, row_data=list(df.values.tolist()), link_column="Map", zip=zip)

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
