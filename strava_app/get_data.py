import requests
import requests_cache
import urllib3
import json
import os
from datetime import datetime
import pandas as pd
import logging
import aiohttp
import asyncio
import time
import math

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests_cache.install_cache('strava_cache', backend='sqlite', expire_after=180)

def roundup(x):
    return int(math.ceil(x / 100.0)) * 100

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
    print('Requesting Token...')
    res = requests.post(auth_url, data=payload, verify=False)
    access_token = res.json()['access_token']
    print(f'Access Token = {access_token}')
    return access_token


def get_athlete(access_token) -> None:
    url = 'https://www.strava.com/api/v3/athlete'
    data = requests.get(url + '?' + 'access_token=' + access_token)
    data = data.json()
    return data


def get_athlete_stats(access_token, athlete_id):
    url =  'https://www.strava.com/api/v3/athletes/'
    data = requests.get(url + str(athlete_id)  + '/stats?' + 'access_token=' + access_token)
    data = data.json()
    # print(json.dumps(data, indent=2))
    return data


def get_activity_ids(access_token):
    url = "https://www.strava.com/api/v3/athlete/activities"

    # Set up a data frame for each activity
    col_names = ['id','type','date']
    activities = pd.DataFrame(columns=col_names)

    # if this is over 20 it doesn't work
    per_page = 100

    page = 1

    # Limit page while testing
    while page < 3:
        print(f'page {page}')

    # code to take all activities
    # while True:
    #     print(f'page {page}')

        # Get activities by page
        data = requests.get(url + '?' + 'access_token=' + access_token + '&per_page=' +str(per_page) + '&page=' + str(page))
        # print(data.from_cache)
        data = data.json()

        for i in range(len(data)):
            print(data[i]['name']) 

        # Print out json for visibility
        # with open('static/all_activities.json', 'w') as f:
        #     json.dump(data, f, indent=2)

        # Exit loop if no results 
        if (not data):
            break
        
        # Otherwise add new data to dataframe
        print(len(data))

        for i in range(len(data)):
            activities.loc[i + (page-1)*per_page,'id'] = data[i]['id']
            activities.loc[i + (page-1)*per_page,'type'] = data[i]['type']
            activities.loc[i + (page-1)*per_page,'date'] = datetime.strptime(data[i]['start_date'][:10], '%Y-%m-%d').date()

        print(f'Page {page} completed')
        page += 1

    print(f'Total rows = {len(activities)}')
    return activities


def get_activity_ids_ASYNC(access_token, total):
    start = time.time()
    url = "https://www.strava.com/api/v3/athlete/activities"

    # Set up a data frame for each activity
    col_names = ['id','type','date']
    activities = pd.DataFrame(columns=col_names)

    # Number of activities to feature in each get request
    per_page = 100

    # Use combined totals of athletes runs, rides, and swims to base how many activities we  will draw from
    # Then double it in case athlete has recorded additional activities like yoga, walking etc
    # Revist this, I ran mine with 10,000 activites compared to my actual of 2,700 and time was same

    # +1 needed as range will run up to but not including
    # pages = math.ceil((total / per_page) * 2) + 1
    pages = 10
    print(f'Pages ={pages}')

    # Will need a way of finding limit or pages, I have 2686 activities
    # Strava should have a totals - yes 'ActivityStats
    loop = asyncio.get_event_loop()
    coroutines = [get(url + '?' + 'access_token=' + access_token + '&per_page=' +str(per_page) + '&page=' + str(page)) for page in range(1, pages)]

    data = loop.run_until_complete(asyncio.gather(*coroutines))
    # Results is a  list and each entry has a json with 100 activities
    print(f'Results length= {len(data)}')

    # Set up a data frame for each activity
    col_names = ['id','type','date']
    activities = pd.DataFrame(columns=col_names)



# update below with try except to stop when no data / out of index range

    k = 0
    for i in range(pages-1): #0 to 1
        for j in range(per_page): #0 to 2
            activities.loc[k,'id'] = data[i][j]['id']
            activities.loc[k,'type'] = data[i][j]['type']
            activities.loc[k,'date'] = datetime.strptime(data[i][j]['start_date'][:10], '%Y-%m-%d').date()
            k += 1

    print(activities)
    end = time.time()
    diff = end-start
    print(f'Per_page= {per_page}, Time={diff}')
    return activities


# This loops through every single activity doing one get request at a time. Very slow, but only way to get all data for activity
def get_activity_data(access_token, activities):
    basic_url = "https://www.strava.com/api/v3/activities"

    # initialise data frame for all activity data excluding laps 
    col_names = ['id', 
                'date',
                'time', 
                'name', 
                'distance', 
                'moving_time', 
                'workout_type', 
                'average_speed', 
                'average_heartrate', 
                'average_cadence',
                'perceived_exertion', 
                'description', 
                'Map']

    activity_data = pd.DataFrame(columns=col_names)

    # filter to only runs
    runs = activities[activities.type == 'Run']

    for i in range(len(runs)):
        run_id = runs['id'][i]

        # Load activity data
        data = requests.get(basic_url + '/' + str(run_id) + '?access_token='+ access_token)
        
        # Check if from cache - works
        # print(data.from_cache)
        print('Loading activity {} out of {}'.format(i,len(runs)))
        data = data.json()


        # Just used once to look in data
        # with open('static/detailed_activity.json', 'w') as f:
        #     json.dump(data, f, indent=2)

        activity_data.loc[i, 'id'] = data['id']
        activity_data.loc[i, 'date'] = datetime.strptime(data['start_date'][:10], '%Y-%m-%d').date()
        activity_data.loc[i, 'time'] = datetime.strptime(data['start_date'], '%Y-%m-%dT%H:%M:%SZ').time()
        activity_data.loc[i, 'name'] = data['name']
        activity_data.loc[i, 'distance'] = data['distance']
        activity_data.loc[i, 'moving_time'] = data['moving_time']
        activity_data.loc[i, 'workout_type'] = data['workout_type']
        activity_data.loc[i, 'average_speed'] = data['average_speed']
        activity_data.loc[i, 'average_heartrate'] = data['average_heartrate']
        activity_data.loc[i, 'average_cadence'] = data['average_cadence']
        activity_data.loc[i, 'description'] = data['description']
        # activity_data.loc[i, 'suffer_score'] = data['suffer_score']
        activity_data.loc[i, 'perceived_exertion'] = data['perceived_exertion']
        activity_data.loc[i, 'Map'] = 'Show Map'

    return activity_data



def get_activity_laps(access_token, activities):

    basic_url = "https://www.strava.com/api/v3/activities"

    # might be easier to use: GET /activities/{id}/laps

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
        # with open('static/detailed_activity.json', 'w') as f:
        #     json.dump(data, f, indent=2)

        # Extract Activity Laps
        activity_laps = pd.DataFrame(data['laps']) 
        activity_laps['id'] = run_id
        activity_laps['date'] = data['start_date']
        
        # Add to total list of splits
        laps = pd.concat([laps, activity_laps])

    return laps

def weekly_totals(activities):




    return 0

def monthly_totals():




    return 0

def yearly_totals():




    return 0


# Drawback here is that json() loads whole response into memory. However, we should not be loading in much data so OK for now?
# Store result in dataframe then free memory
async def get(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
            # return response


def get_activity_data_TEST(access_token, activities) -> None:
    basic_url = "https://www.strava.com/api/v3/activities"

    # initialise data frame for all activity data excluding laps 
    col_names = ['id', 
                'date',
                'time', 
                'name', 
                'distance', 
                'moving_time', 
                'workout_type', 
                'average_speed', 
                'average_heartrate', 
                'average_cadence',
                'perceived_exertion', 
                'description', 
                'Map']

    activity_data = pd.DataFrame(columns=col_names)

    # filter to only runs
    runs = activities[activities.type == 'Run']

    # for i in range(len(runs)):
    #     run_id = runs['id'][i]

        # Load activity data
        # data = requests.get(basic_url + '/' + str(run_id) + '?access_token='+ access_token)
        
        # # Check if from cache - works
        # # print(data.from_cache)
        # print('Loading activity {} out of {}'.format(i,len(runs)))
        # data = data.json()

    print(len(runs))
    loop = asyncio.get_event_loop()
    coroutines = [get(basic_url + '/' + str(runs['id'][i]) + '?access_token='+ access_token) for i in range(len(runs))]

    # coroutines = [get("http://example.com") for _ in range(8)]

    results = loop.run_until_complete(asyncio.gather(*coroutines))

    # print(results[0])
    # print(json.dumps(results[0], indent=4))
    # return results[0]
    # print("Results: %s" % results)



# Testing
access_token = get_access_token()
athlete_id = get_athlete(access_token)['id']
print(athlete_id)
athlete_stats = get_athlete_stats(access_token, athlete_id)
total_activities  = total_activities = athlete_stats['all_ride_totals']['count'] + athlete_stats['all_run_totals']['count'] + athlete_stats['all_swim_totals']['count']
print(total_activities)
activity_ids = get_activity_ids_ASYNC(access_token, total_activities)


# activity_ids = get_activity_ids(access_token)
# activity_data = get_activity_data_TEST(access_token, activity_ids)
# activity_laps = get_activity_laps(access_token, activity_ids)
# print(activity_data)
