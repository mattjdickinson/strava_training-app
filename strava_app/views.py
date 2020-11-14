from datetime import datetime
from flask import Flask, render_template
from . import app
import requests
import urllib3
import json
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# from get_data import get_dataset

def get_dataset():
    auth_url = "https://www.strava.com/oauth/token"
    activities_url = "https://www.strava.com/api/v3/athlete/activities"

    payload = {
        'client_id': os.environ.get('CLIENT_ID'),
        'client_secret': os.environ.get('CLIENT_SECRET'),
        'refresh_token': os.environ.get('REFRESH_TOKEN'),
        'grant_type': "refresh_token",
        'f': 'json'
    }

    # Refresh token obtained through authorisation code from read_all activities (different to strava default of 'read'). Refresh_token doens't change. See 'activity_readall.txt' for steps
    print("Requesting Token...\n")
    res = requests.post(auth_url, data=payload, verify=False)
    # print(res.json())
    access_token = res.json()['access_token']
    print("Access Token = {}\n".format(access_token))

    header = {'Authorization': 'Bearer ' + access_token}
    param = {'per_page': 200, 'page': 1}
    # imports as list
    data = requests.get(activities_url, headers=header, params=param).json()

    return data


@app.route("/")
def home():
    data = get_dataset()
    return render_template("home.html", data = data)

@app.route("/about/")
def about():
    return render_template("about.html")

@app.route("/api/")
def api():
    my_dataset = get_dataset()

    return render_template("api.html", data=my_dataset)

# @app.route("/api/data")
# def get_data():

#     return app.send_static_file("data.json")
