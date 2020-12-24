from datetime import datetime, time
from flask import Flask, render_template
from . import app
import requests
import requests_cache
import urllib3
import json
import os
from .get_data import get_access_token, get_athlete, get_athlete_stats, get_activity_ids, get_activity_data, weekly_totals, format_timedelta_to_HHMMSS, monthly_totals
import asyncio
import plotly.graph_objects as go
from plotly.subplots import make_subplots

requests_cache.install_cache('strava_cache', backend='sqlite', expire_after=180)

# when add in authorise code, then we want to pull api and cache, so will need new route

@app.route("/")
def home():

    #Default to  True.  Has set code so that 100 pulls per 15mins API limit won't be breached. Add toggle to website
    use_stored_data = True

    if use_stored_data:
        # dummy values  to pass into subsequent functions
        access_token = 'xxx'
        athlete_id = 'xxx'
    else:
        access_token = get_access_token()
        athlete_id = get_athlete(access_token)['id']

    athlete_stats = get_athlete_stats(access_token, athlete_id, use_stored_data)
    total_activities  = total_activities = athlete_stats['all_ride_totals']['count'] + athlete_stats['all_run_totals']['count'] + athlete_stats['all_swim_totals']['count']
    activity_ids = get_activity_ids(access_token, total_activities, use_stored_data)

    #Need to run to get live data for past 100 so have them stored for demo, set below True to False, and date range to start 1/9/2020
    start_date =  datetime(2020, 10, 1).date()
    end_date = datetime(2020, 12, 31).date()

    activity_data, activity_laps = get_activity_data(access_token, activity_ids, start_date, end_date, use_stored_data)
    weekly = weekly_totals(activity_data)

    # This function works in get.data.py, but when it is run in here, the '0 days' gets displayed in home.html
    activity_data.moving_time = activity_data.moving_time.apply(lambda x: format_timedelta_to_HHMMSS(x))

    column_names = ['Date',
                    'Day', 
                    'Time', 
                    'Name', 
                    'Distance (miles)', 
                    'Run Time (h:m:s)', 
                    'Type', 
                    'Average Pace (/mi)', 
                    'Laps (Dist, Time, Avg Pace)',
                    'Average Heart Rate', 
                    'Average Cadence (spm)',
                    'Effort (1-10)', 
                    'Notes']



    return render_template("home.html", column_names=column_names, activity_data=activity_data, weekly_totals=weekly)

@app.route("/weekly/")
def weekly():
    # Default to True since user directed to Home first which would pull latest data
    use_stored_data = True

    if use_stored_data:
        # dummy values  to pass into subsequent functions
        access_token = 'xxx'
        athlete_id = 'xxx'
    else:
        access_token = get_access_token()
        athlete_id = get_athlete(access_token)['id']

    athlete_stats = get_athlete_stats(access_token, athlete_id, use_stored_data)
    total_activities  = total_activities = athlete_stats['all_ride_totals']['count'] + athlete_stats['all_run_totals']['count'] + athlete_stats['all_swim_totals']['count']
    activity_ids = get_activity_ids(access_token, total_activities, use_stored_data)
    runs = activity_ids[(activity_ids.type == 'Run')]
    weekly = weekly_totals(runs)

    # Default to past year as too many x-axis labels otherwise
    start_date =  datetime(2020, 1, 1).date()

    labels = weekly['wc'][weekly.wc >= start_date]
    values = weekly['distance'][weekly.wc >= start_date]

    bar_labels=labels
    bar_values=values

    return render_template("weekly.html", title='Miles per week', max=100, labels=bar_labels, values=bar_values)


@app.route("/monthly/")
def monthly():

    # Default to True since user directed to Home first which would pull latest data
    use_stored_data = True

    if use_stored_data:
        # dummy values  to pass into subsequent functions
        access_token = 'xxx'
        athlete_id = 'xxx'
    else:
        access_token = get_access_token()
        athlete_id = get_athlete(access_token)['id']



    athlete_stats = get_athlete_stats(access_token, athlete_id, use_stored_data)
    total_activities  = total_activities = athlete_stats['all_ride_totals']['count'] + athlete_stats['all_run_totals']['count'] + athlete_stats['all_swim_totals']['count']
    activity_ids = get_activity_ids(access_token, total_activities, use_stored_data)
    runs = activity_ids[(activity_ids.type == 'Run')]
    
    # Causes assertion error if the below line is omitted. Don't know why
    weekly = weekly_totals(runs)

    monthly = monthly_totals(runs)
    labels = monthly['month_start']
    values = monthly['distance'] 

    bar_labels=labels
    bar_values=values
    return render_template("monthly.html", title='Monthly mileage', max=500, labels=bar_labels, values=bar_values)
    

# https://developers.strava.com/docs/authentication/
@app.route("/authorized/")
def get_code():
    
    return render_template("api.html")


