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
    basic_url = "https://www.strava.com/api/v3/activities"

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

    # Set up a data frame for each activity
    col_names = ['id','type','date']
    activities = pd.DataFrame(columns=col_names)

    per_page = 1
    page = 1

    # Limit to 1 page while testing
    while page == 1:
    
    # code to take all activities
    # while True:
        
        # Get activities by page
        header = {'Authorization': 'Bearer ' + access_token}
        param = {'per_page': per_page, 'page': page}
        data = requests.get(activities_url, headers=header, params=param).json()

        # Exit loop if no results 
        if (not data):
            break
        
        # Otherwise add new data to dataframe
        for i in range(len(data)):
            activities.loc[i + (page-1)*per_page,'id'] = data[i]['id']
            activities.loc[i + (page-1)*per_page,'type'] = data[i]['type']
            activities.loc[i + (page-1)*per_page,'date'] = datetime.strptime(data[i]['start_date'][:10], '%Y-%m-%d').date()

        page += 1

    # initialise data frame for data we want to show

    # Sample code to get json for one activity to see what working with
    # filter to only runs
    runs = activities[activities.type == 'Run']
    # loop through each activity id and retrieve data
    for run_id in runs['id']:
        # Load activity data
        print(run_id)
        # access_token_str = "access_token=+ +448dd068c95485c6c1e0c5adbfaa69496cbb505f" 
        # print(basic_url + '/' + str(run_id) + '?access_token='+ access_token)
        r = requests.get(basic_url + '/' + str(run_id) + '?access_token='+ access_token)
        r = r.json()
        # print(json.dumps(r, indent=2))
        # print(json.dumps(r['description'], indent=2))


    lap_index = 1
    while True:
        
        if (not r['laps'][lap_index]):
            break

        # print(r['laps'][lap_index])
        print(json.dumps(r['laps'][lap_index], indent=2))
        lap_index += 1

    # Laps are the manual splits, loop through lap_index while True "laps['lap_index']


    return activities

data = get_dataset()
# print(data)


# https://www.strava.com/api/v3/activities/4323804440?access_token=a611269bc4a17143e5fc9e4a7648180f16102c5d
# https://www.strava.com/api/v3/athlete/activities/4342550306?access_token=a611269bc4a17143e5fc9e4a7648180f16102c5d