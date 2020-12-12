import requests
import requests_cache
import urllib3
import json
import os
from datetime import datetime, timedelta, date
import pandas as pd
import logging
import aiohttp
import asyncio
import time
import math

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests_cache.install_cache('strava_cache', backend='sqlite', expire_after=180)


M_TO_MILES = 0.000621371
M_TO_KM = 1000
# minutes per second to minute per mile, 1mps = 26.8224 min/mile
MPS_TO_MPM = 26.8224
MPS_TO_MPK = 16.66666667


def roundup(x):
    return int(math.ceil(x / 100.0)) * 100


def mps_to_mpk(speed):
    global MPS_TO_MPM
    m, s = divmod(MPS_TO_MPM  / speed*60, 60)
    pace = f'{int(m):02d}:{int(s)+1:02d}'
    return pace

def workout_type(i):
    type = {0 : 'None',
            1: "Race",
            2: "Long Run",
            3: "Workout"}
    return type[i]

# Drawback here is that json() loads whole response into memory. However, we should not be loading in much data so OK for now?
# Store result in dataframe then free memory
async def get(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
            # return response


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


def get_athlete(access_token):
    url = 'https://www.strava.com/api/v3/athlete'
    data = requests.get(url + '?' + 'access_token=' + access_token)
    data = data.json()
    return data


def get_athlete_stats(access_token, athlete_id, use_stored_data):
    if use_stored_data:
        with open('strava_app/static/get_athlete_stats.json', 'r') as file:
            data = json.load(file)
    else:
        url =  'https://www.strava.com/api/v3/athletes/'
        data = requests.get(url + str(athlete_id)  + '/stats?' + 'access_token=' + access_token)
        data = data.json()
        with open('strava_app/static/get_athlete_stats.json', 'w') as file:
            json.dump(data, file, indent=4, sort_keys=True)
    return data


def get_activity_ids(access_token, total, use_stored_data):
    start = time.time()

    # Set up a data frame for each activity
    col_names = ['id','type','date']
    activities = pd.DataFrame(columns=col_names)

    # Number of activities to feature in each get request. High limit to reduce number of API calls
    per_page = 10

    # Use combined totals of athletes runs, rides, and swims to base how many activities we  will draw from
    # Then double it in case athlete has recorded additional activities like yoga, walking etc

    # +1 needed as range will run up to but not including
    # pages = math.ceil((total / per_page) * 2) + 1
    pages = 3
    print(f'Pages = {pages}')

    if use_stored_data:
        with open('strava_app/static/get_activity_ids.json', 'r') as file:
            data = json.load(file)

    else:
        url = "https://www.strava.com/api/v3/athlete/activities"

        col_names = ['id','type','date']
        activities = pd.DataFrame(columns=col_names)

        asyncio.set_event_loop(asyncio.SelectorEventLoop()) # need this line so that runs in flask. Looks like bug with new event policy in Python 3.8
        loop = asyncio.get_event_loop()
        coroutines = [get(url + '?' + 'access_token=' 
                        + access_token + '&per_page=' +str(per_page) 
                        + '&page=' + str(page)) for page in range(1, pages)]

        data = loop.run_until_complete(asyncio.gather(*coroutines))

        # Save down in static file to read in when developing
        with open('strava_app/static/get_activity_ids.json', 'w') as file:
            json.dump(data, file, indent=4, sort_keys=True)

        # Results is a  list and each entry has a json with 100 activities
        print(f'Results length= {len(data)}')

    k = 0
    for i in range(pages-1):
        for j in range(per_page):
            try:
                activities.loc[k,'id'] = data[i][j]['id']
                activities.loc[k,'type'] = data[i][j]['type']
                activities.loc[k,'date'] = datetime.strptime(data[i][j]['start_date'][:10], '%Y-%m-%d').date()
                k += 1
            except: # no data to parse
                break

    # print(activities)
    end = time.time()
    print(f'Time={end-start}')
    return activities


def get_activity_data(access_token, activities, start_date, end_date, use_stored_data):
    global M_TO_MILES
    global MPS_TO_MPM    
    
    start = time.time()

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

    # initialize dataframe for laps data
    col_names = ['id','date']
    laps = pd.DataFrame(columns=col_names)

    # Need to limit to 100 per 15min..


    runs = activities[(activities.type == 'Run') & (activities.date >= start_date) & (activities.date <= end_date)]

    if use_stored_data:
        with open('strava_app/static/get_activity_data.json', 'r') as file:
            data = json.load(file)

    else:
        basic_url = "https://www.strava.com/api/v3/activities"
        asyncio.set_event_loop(asyncio.SelectorEventLoop())
        loop = asyncio.get_event_loop()
        coroutines = [get(basic_url + '/' + str(runs['id'][i]) + '?access_token='+ access_token) for i in range(len(runs))]
        data = loop.run_until_complete(asyncio.gather(*coroutines))

        # Save down in static file to read in when developing
        with open('strava_app/static/get_activity_data.json', 'w') as file:
            json.dump(data, file, indent=4, sort_keys=True)

    print(len(runs))
    for i in range(len(runs)):
        try:
            activity_data.loc[i, 'id'] = data[i]['id']
            activity_data.loc[i, 'date'] = datetime.strptime(data[i]['start_date'][:10], '%Y-%m-%d').date()
            activity_data.loc[i, 'time'] = datetime.strptime(data[i]['start_date'], '%Y-%m-%dT%H:%M:%SZ').time()
            activity_data.loc[i, 'name'] = data[i]['name']
            activity_data.loc[i, 'distance'] = '{:.2f}'.format(data[i]['distance'] * M_TO_MILES)
            activity_data.loc[i, 'moving_time'] = str(timedelta(seconds=data[i]['moving_time']))
            activity_data.loc[i, 'workout_type'] = workout_type(data[i]['workout_type'])
            activity_data.loc[i, 'average_speed'] = mps_to_mpk(data[i]['average_speed'])
            activity_data.loc[i, 'average_heartrate'] = data[i]['average_heartrate']
            activity_data.loc[i, 'average_cadence'] = data[i]['average_cadence']
            activity_data.loc[i, 'description'] = data[i]['description']
            activity_data.loc[i, 'perceived_exertion'] = int(data[i]['perceived_exertion'])
            activity_data.loc[i, 'Map'] = 'Show Map'
            activity_data['grp_idx'] = activity_data['date'].apply(lambda x: '%s-%s' % (x.year, 'W{:02d}'.format(x.isocalendar()[1])))

            # Extract Activity Laps
            activity_laps = pd.DataFrame(data[i]['laps']) 
            activity_laps['id'] = data[i]['id']
            activity_laps['date'] = datetime.strptime(data[i]['start_date'][:10], '%Y-%m-%d').date()
            
            # Add to total list of splits
            laps = pd.concat([laps, activity_laps])
        except:
            break

    


    # We don't need all of laps, so after this we can drop what we don't need
    laps = laps.drop(['resource_state', 'activity',  'athlete', 'elapsed_time', 'start_date', 'start_date_local', 'start_index', 
                            'end_index', 'total_elevation_gain', 'max_speed',  'average_cadence', 'average_heartrate', 
                            'max_heartrate', 'lap_index',  'split', 'pace_zone'], axis=1)


    laps['moving_time'] = laps['moving_time'].map(lambda a: str(timedelta(seconds=a)))
    laps['distance'] = laps['distance'].map(lambda a: a * M_TO_MILES)
    laps['average_speed'] = laps['average_speed'].map(lambda a: mps_to_mpk(a))

    end = time.time()
    print(f'Time={end-start}')
    return activity_data, laps


# https://stackoverflow.com/questions/51750077/iterate-over-pd-df-with-date-column-by-week-python/51750811


def from_year_week_to_date(d):
    date = datetime.strptime(d + '-1', "%G-W%V-%u")
    return date

def make_delta(entry):
    h, m, s = entry.split(':')
    return datetime.timedelta(hours=int(h), minutes=int(m), seconds=int(s))

def td_format(td_object):
    seconds = int(td_object.total_seconds())
    periods = [
        ('year',        60*60*24*365),
        ('month',       60*60*24*30),
        ('day',         60*60*24),
        ('hour',        60*60),
        ('minute',      60),
        ('second',      1)
    ]

    strings=[]
    for period_name, period_seconds in periods:
        if seconds > period_seconds:
            period_value , seconds = divmod(seconds, period_seconds)
            has_s = 's' if period_value > 1 else ''
            strings.append("%s %s%s" % (period_value, period_name, has_s))

    return ", ".join(strings)


def weekly_totals(df):
    df['moving_time'] = pd.to_timedelta(df['moving_time']) #was activity_data

    dist = df.groupby(['grp_idx'])['distance'].sum().reset_index(name='distance')
    time = df.groupby(['grp_idx'])['moving_time'].sum().reset_index(name='time')
    print(time)
    # time['time'] = time['time'].apply(lambda x: '{%H:%M:%S}'.format(x))
    time['time'] = time['time'].apply(lambda x: td_format(x))

    print(time)
    # time['time'] = time['time'].applymap('{%H:%M:%SZ}'.format)
    # print(time)
    w_totals = pd.merge(dist, time, how='left', on='grp_idx')

    
    return w_totals



def monthly_totals():




    return 0


def yearly_totals():




    return 0


# Testing
# use_stored_data = False
# access_token = get_access_token()
# athlete_id = get_athlete(access_token)['id']
# athlete_stats = get_athlete_stats(access_token, athlete_id, True)
# total_activities  = total_activities = athlete_stats['all_ride_totals']['count'] + athlete_stats['all_run_totals']['count'] + athlete_stats['all_swim_totals']['count']
# activity_ids = get_activity_ids(access_token, total_activities, True)
# activity_data, laps = get_activity_data(access_token, activity_ids, True)
# print(activity_data.head())
# print(laps)




# df = weekly_totals(activity_data)
# print(df)

# df = pd.to_timedelta(activity_data['moving_time'])
# print(df.sum())



# # df = df.applymap(lambda entry: make_delta(entry))
# print(df)




# d = "2020-W49"
# r = datetime.strptime(d + '-1', "%G-W%V-%u")
# print(r)
# print(from_year_week_to_date(d))

