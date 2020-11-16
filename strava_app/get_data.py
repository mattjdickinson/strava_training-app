import requests
import urllib3
import json
import os
from datetime import datetime
import pandas as pd

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_access_token():
    auth_url = "https://www.strava.com/oauth/token"

    payload = {
        'client_id': os.environ.get('CLIENT_ID'),
        'client_secret': os.environ.get('CLIENT_SECRET'),
        'refresh_token': os.environ.get('REFRESH_TOKEN'),
        'grant_type': "refresh_token",
        'f': 'json'
    }

    # Refresh token obtained through authorisation code from read_all activities (different to strava default of 'read'). 
    # Refresh_token doens't change. See 'activity_readall.txt' for steps
    print("Requesting Token...\n")
    res = requests.post(auth_url, data=payload, verify=False)
    access_token = res.json()['access_token']
    print("Access Token = {}\n".format(access_token))
    return access_token


def get_activity_ids(access_token):
    activities_url = "https://www.strava.com/api/v3/athlete/activities"

    # Set up a data frame for each activity
    col_names = ['id','type','date']
    activities = pd.DataFrame(columns=col_names)

    per_page = 3
    page = 1

    # Limit to 1 page while testing
    while page == 1:
    
    # code to take all activities
    # while True:
        
        # Get activities by page
        header = {'Authorization': 'Bearer ' + access_token}
        param = {'per_page': per_page, 'page': page}
        data = requests.get(activities_url, headers=header, params=param).json()

        # Print out json for visibility
        # with open('static/all_activities.json', 'w') as f:
        #     json.dump(data, f, indent=2)

        # Exit loop if no results 
        if (not data):
            break
        
        # Otherwise add new data to dataframe
        for i in range(len(data)):
            activities.loc[i + (page-1)*per_page,'id'] = data[i]['id']
            activities.loc[i + (page-1)*per_page,'type'] = data[i]['type']
            activities.loc[i + (page-1)*per_page,'date'] = datetime.strptime(data[i]['start_date'][:10], '%Y-%m-%d').date()

        page += 1

    return activities


def get_activity_data(access_token, activities):
    basic_url = "https://www.strava.com/api/v3/activities"

    # initialise data frame for all activity data excluding laps 
    col_names = ['id', 'start_date', 'name', 'distance', 'moving_time' 'workout_type', 'average_speed', 'average_heartrate', 'average_cadence', 'description', 'suffer_score', 'perceived_exertion']
    activity_data = pd.DataFrame(columns=col_names)

    # filter to only runs
    runs = activities[activities.type == 'Run']

    for i in range(len(runs)):
        run_id = runs['id'][i]

        # Load activity data
        data = requests.get(basic_url + '/' + str(run_id) + '?access_token='+ access_token)
        data = data.json()

        # Just used once to look in data
        with open('static/detailed_activity.json', 'w') as f:
            json.dump(data, f, indent=2)

        activity_data.loc[i, 'id'] = data['id']
        activity_data.loc[i, 'start_date'] = datetime.strptime(data['start_date'][:10], '%Y-%m-%d').date()
        activity_data.loc[i, 'name'] = data['name']
        activity_data.loc[i, 'distance'] = data['distance']
        activity_data.loc[i, 'moving_time'] = data['moving_time']
        activity_data.loc[i, 'workout_type'] = data['workout_type']
        activity_data.loc[i, 'average_speed'] = data['average_speed']
        activity_data.loc[i, 'average_heartrate'] = data['average_heartrate']
        activity_data.loc[i, 'average_cadence'] = data['average_cadence']
        activity_data.loc[i, 'description'] = data['description']
        activity_data.loc[i, 'suffer_score'] = data['suffer_score']
        activity_data.loc[i, 'perceived_exertion'] = data['perceived_exertion']
        activity_data.loc[i, 'moving_time'] = data['moving_time']

        # i =+ 1

    return activity_data

def get_activity_laps(access_token, activities):

    basic_url = "https://www.strava.com/api/v3/activities"

    # initialize dataframe for laps data
    col_names = ['id','date']
    laps = pd.DataFrame(columns=col_names)

    # filter to only runs
    runs = activities[activities.type == 'Run']

    # loop through each activity id and retrieve data
    for run_id in runs['id']:
        # print(run_id)

        # Load activity data
        data = requests.get(basic_url + '/' + str(run_id) + '?access_token='+ access_token)
        data = data.json()

        # Just used once to look in data
        with open('static/detailed_activity.json', 'w') as f:
            json.dump(data, f, indent=2)

        # Extract Activity Laps
        activity_laps = pd.DataFrame(data['laps']) 
        activity_laps['id'] = run_id
        activity_laps['date'] = data['start_date']
        
        # Add to total list of splits
        laps = pd.concat([laps, activity_laps])

    return laps

access_token = get_access_token()
activity_ids = get_activity_ids(access_token)
activity_data = get_activity_data(access_token, activity_ids)
activity_laps = get_activity_laps(access_token, activity_ids)
print(activity_data)
