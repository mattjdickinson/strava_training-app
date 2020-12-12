from datetime import datetime
from flask import Flask, render_template
from . import app
import requests
import requests_cache
import urllib3
import json
import os
from .get_data import get_access_token, get_athlete, get_athlete_stats, get_activity_ids, get_activity_data, get
import asyncio

requests_cache.install_cache('strava_cache', backend='sqlite', expire_after=180)

# when add in authorise code, then we want to pull api and cache, so will need new route

@app.route("/")
def home():
    use_stored_data = True

    start_date =  datetime(2020, 1, 1).date()
    end_date = datetime(2020, 12, 31).date()

    access_token = get_access_token()
    athlete_id = get_athlete(access_token)['id']
    athlete_stats = get_athlete_stats(access_token, athlete_id, use_stored_data)
    total_activities  = total_activities = athlete_stats['all_ride_totals']['count'] + athlete_stats['all_run_totals']['count'] + athlete_stats['all_swim_totals']['count']
    activity_ids = get_activity_ids(access_token, total_activities, use_stored_data)
    activity_data, activity_laps = get_activity_data(access_token, activity_ids, start_date, end_date, use_stored_data)

    column_names = ['Date', 
                    'Time', 
                    'Name', 
                    'Distance (miles)', 
                    'Run Time', 
                    'Type', 
                    'Average Pace', 
                    'Laps (Number, Distance, Time, Average Pace)',
                    'Average Heart Rate', 
                    'Average Cadence',
                    'Effort (1-10)', 
                    'Notes']

    # send dataframe to list of dicts t0 make referencing in html easier
    data = activity_data.T.to_dict().values()
    laps = activity_laps.T.to_dict().values()
    return render_template("home.html", column_names=column_names, activity_data=data, laps=laps)

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

