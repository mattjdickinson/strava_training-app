import requests
import urllib3
import json
import os
from datetime import datetime
import pandas as pd

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

    # Refresh token obtained through authorisation code from read_all activities (different to strava default of 'read'). 
    # Refresh_token doens't change. See 'activity_readall.txt' for steps
    print("Requesting Token...\n")
    res = requests.post(auth_url, data=payload, verify=False)
    # print(res.json())
    access_token = res.json()['access_token']
    print("Access Token = {}\n".format(access_token))

    header = {'Authorization': 'Bearer ' + access_token}
    param = {'per_page': 200, 'page': 1}
    data = requests.get(activities_url, headers=header, params=param).json()

    # http://www.hainke.ca/index.php/2018/08/23/using-the-strava-api-to-retrieve-activity-data/

    # print(type(my_dataset)) # List of dicts (name, value pairs)
    # print(json.dumps(data, indent=2))

    # Get encoded polyline for use in google maps platform polyline
    # https://developers.google.com/maps/documentation/utilities/polylineutility

    # run_id = 4323804440
    # r = requests.get(activities_url + '/' + str(run_id) + '?' + 'access_token="' + access_token + '"')
    # r = r.json()
    # print(r)


    return data

def get_data_splits():
    # Initialize the dataframe
    col_names = ['id','type']
    activities = pd.DataFrame(columns=col_names)

    access_token = "access_token=a611269bc4a17143e5fc9e4a7648180f16102c5d" # replace with your access token here
    url = "https://www.strava.com/api/v3/activities"

    page = 1

    # while True:
        
    # get page of activities from Strava
    r = requests.get(url + '?' + access_token + '&per_page=6' + '&page=' + str(page))
    r = r.json()

    # # if no results then exit loop
    # if (not r):
    #     break
    
    # otherwise add new data to dataframe
    for x in range(len(r)):
        activities.loc[x + (page-1)*50,'id'] = r[x]['id']
        activities.loc[x + (page-1)*50,'type'] = r[x]['type']

        # # increment page
        # page += 1

        # filter to only runs
    runs = activities[activities.type == 'Run']

    # initialize dataframe for split data
    col_names = ['average_speed','distance','elapsed_time','elevation_difference','moving_time','pace_zone', 'split','id','date']
    splits = pd.DataFrame(columns=col_names)

    # loop through each activity id and retrieve data
    for run_id in runs['id']:
        
        # Load activity data
        print(run_id)
        print(url + '/' + str(run_id) + '?' + access_token)
        r = requests.get(url + '/' + str(run_id) + '?' + access_token)
        r = r.json()
        print(json.dumps(r['description'], indent=2))

        # Extract Activity Splits
        activity_splits = pd.DataFrame(r['splits_metric']) 
        activity_splits['id'] = run_id
        activity_splits['date'] = r['start_date']
        
        # Add to total list of splits
        splits = pd.concat([splits, activity_splits])

    return splits



# Testing 
# data = get_dataset()
data = get_data_splits()
# print(get_data_splits())
# print(json.dumps(data[4], indent=2))
# print(type(data[1]['start_date']))

# print(data[4]['name'])
# print(data[1]['start_date'])
# print(datetime.strptime(data[1]['start_date'][:10], '%Y-%m-%d'))
# str_to_dt = datetime.strptime(data[1]['start_date'], '%Y-%m-%dT%H:%M:%SZ')
# date = str_to_dt.date()
# time = str_to_dt.time()
# print(date)
# print(time)


# for activity in data:
#     print(activity['name'], activity['description'])

# print(data[1]['map']['summary_polyline'])

