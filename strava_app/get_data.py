import requests
import requests_cache
import urllib3
import json
import os
from datetime import datetime, timedelta, date, time
import pandas as pd
import logging
import aiohttp
import asyncio
# import time
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


def mps_to_mpm(speed):
    global MPS_TO_MPM
    m, s = divmod(MPS_TO_MPM  / speed*60, 60)
    pace = f'{int(m):2d}:{int(s)+1:02d}'
    return pace

def workout_type(i):
    type = {0 : 'None',
            1: "Race",
            2: "Long Run",
            3: "Workout"}
    return type[i]

def am_or_pm(i):
    # txt = i.split(':')
    # tm = time(txt[0], txt[1], txt[2])
    if i < time(12,00,00,00):
        x = 'AM'
    else:
        x = 'PM'
    return x


# Drawback here is that json() loads whole response into memory. However, we should not be loading in much data so OK for now?
# Store result in dataframe then free memory
async def get(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()



def authroise_user():
    auth_url = "https://www.strava.com/oauth/authorize"
    redirect_uri = "http://localhost:8080/authorized"
    return 0



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
    # start = time.time()
    global M_TO_MILES
    # Set up a data frame for each activity
    col_names = ['id','type','date', 'distance', 'moving_time']
    activities = pd.DataFrame(columns=col_names)

    # Number of activities to feature in each get request. High limit to reduce number of API calls
    per_page = 150

    # Use combined totals of athletes runs, rides, and swims to base how many activities we  will draw from
    # Then double it in case athlete has recorded additional activities like yoga, walking etc

    # +1 needed as range will run up to but not including
    # pages = math.ceil((total / per_page) * 2) + 1
    pages = 11
    # print(f'Pages = {pages}')

    if use_stored_data:
        with open('strava_app/static/get_activity_ids.json', 'r') as file:
            data = json.load(file)

    else:
        url = "https://www.strava.com/api/v3/athlete/activities"

        col_names = ['id','type','date', 'distance', 'moving_time']
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

        # Results is a list and each entry has a json with 100 activities
        print(f'Results length= {len(data)}')

    k = 0
    for i in range(pages-1):
        for j in range(per_page):
            try:
                activities.loc[k,'id'] = data[i][j]['id']
                activities.loc[k,'type'] = data[i][j]['type']
                activities.loc[k,'date'] = datetime.strptime(data[i][j]['start_date'][:10], '%Y-%m-%d').date()
                activities.loc[k, 'distance'] = data[i][j]['distance'] * M_TO_MILES
                activities.loc[k, 'moving_time'] = timedelta(seconds=data[i][j]['moving_time'])

                k += 1
            except: # no data to parse
                break
    activities['grp_idx'] = activities['date'].apply(lambda x: '%s-%s' % (x.year, 'W{:02d}'.format(x.isocalendar()[1])))
    # print(activities)
    # end = time.time()
    # print(f'Time={end-start}')
    return activities


def get_activity_data(access_token, activities, start_date, end_date, use_stored_data):
    global M_TO_MILES
    global MPS_TO_MPM    
    
    # start = time.time()

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
                'laps'
                'Map']

    activity_data = pd.DataFrame(columns=col_names)

    # initialize dataframe for laps data
    col_names = ['id','date']
    laps = pd.DataFrame(columns=col_names)

    runs = activities[(activities.type == 'Run') & (activities.date >= start_date) & (activities.date <= end_date)]
    # print(len(runs))
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
    
    # for i in range(len(runs)):
    # Limiting to 80 as Strava API limits to 100 requests per 15min
    for i in range(70):    
        dt = datetime.strptime(data[i]['start_date'][:10], '%Y-%m-%d').date()
        td = timedelta(seconds=data[i]['moving_time'])
        activity_data.loc[i, 'id'] = data[i]['id']
        activity_data.loc[i, 'date'] = dt
        activity_data.loc[i, 'time'] = am_or_pm(datetime.strptime(data[i]['start_date'], '%Y-%m-%dT%H:%M:%SZ').time())
        activity_data.loc[i, 'name'] = data[i]['name']
        activity_data.loc[i, 'distance'] = data[i]['distance'] * M_TO_MILES
        activity_data.loc[i, 'moving_time'] = td
        # activity_data.loc[i, 'moving_time'] = str(format_timedelta_to_HHMMSS(td))
        # print(format_timedelta_to_HHMMSS(activity_data.loc[i, 'moving_time']))

        activity_data.loc[i, 'Map'] = 'Show Map'

        try:
            activity_data.loc[i, 'workout_type'] = workout_type(data[i]['workout_type'])
        except:
            activity_data.loc[i, 'workout_type'] = 'None'

        try:
            activity_data.loc[i, 'average_speed'] = mps_to_mpm(data[i]['average_speed']) + ' /mi'
        except:
            activity_data.loc[i, 'average_speed'] = activity_data.loc[i, 'distance']  /   td

        try:
            activity_data.loc[i, 'average_heartrate'] = data[i]['average_heartrate']
        except:
            activity_data.loc[i, 'average_heartrate'] = ''

        try:
            activity_data.loc[i, 'average_cadence'] = data[i]['average_cadence'] * 2
        except:
            activity_data.loc[i, 'average_cadence'] = ''

        try:
            activity_data.loc[i, 'description'] = data[i]['description']
        except:
            activity_data.loc[i, 'description'] = ''

        try:
            activity_data.loc[i, 'perceived_exertion'] = int(data[i]['perceived_exertion'])
        except:
            activity_data.loc[i, 'perceived_exertion'] = '-'

        try:
            for j in range(len(data[i]['laps'])):
                name = data[i]['laps'][j]['name']
                distance = '{:.2f}'.format(data[i]['laps'][j]['distance']  * M_TO_MILES)
                moving_time = str(timedelta(seconds=data[i]['laps'][j]['moving_time']))
                pace = mps_to_mpm(data[i]['laps'][j]['average_speed'])

                if j == 0:
                    all_laps = name + '   ' + distance + ' mi  ' + moving_time + '  ' + pace + '/mi'
                elif j < 9:
                    all_laps = all_laps + '\n' + name + '   ' + distance + ' mi  ' + moving_time + '  ' + pace + '/mi'
                else:
                    all_laps = all_laps + '\n' + name + '  ' + distance + ' mi  ' + moving_time + '  ' + pace + '/mi'

            activity_data.loc[i, 'laps'] = all_laps

        except:
            activity_data.loc[i, 'laps'] = all_laps

        try:
            # Extract Activity Laps
            activity_laps = pd.DataFrame(data[i]['laps']) 
            activity_laps['id'] = data[i]['id']
            activity_laps['date'] = datetime.strptime(data[i]['start_date'][:10], '%Y-%m-%d').date()
            
            # Add to total list of splits
            laps = pd.concat([laps, activity_laps])

        except Exception:
            pass

    activity_data['grp_idx'] = activity_data['date'].apply(lambda x: '%s-%s' % (x.year, 'W{:02d}'.format(x.isocalendar()[1])))

    # We don't need all of laps, so after this we can drop what we don't need
    laps = laps.drop(['resource_state', 'activity',  'athlete', 'elapsed_time', 'start_date', 'start_date_local', 'start_index', 
                            'end_index', 'total_elevation_gain', 'max_speed',  'average_cadence', 'average_heartrate', 
                            'max_heartrate', 'lap_index',  'split', 'pace_zone'], axis=1)


    laps['moving_time'] = laps['moving_time'].map(lambda a: str(timedelta(seconds=a)))
    laps['distance'] = laps['distance'].map(lambda a: '{:.2f}'.format(a * M_TO_MILES))
    laps['average_speed'] = laps['average_speed'].map(lambda a: mps_to_mpm(a))

    # end = time.time()
    # print(f'Time={end-start}')
    print(activity_data.head())
    return activity_data, laps


def from_year_week_to_date(d):
    date = datetime.strptime(d + '-1', "%G-W%V-%u")
    return date


def make_delta(entry):
    h, m, s = entry.split(':')
    return timedelta(hours=int(h), minutes=int(m), seconds=int(s))
    # return datetime.timedelta(hours=int(h), minutes=int(m), seconds=int(s))


def td_format(td_object):
    seconds = int(td_object.total_seconds())
    periods = [
        ('yr',        60*60*24*365),
        ('mth',       60*60*24*30),
        ('day',         60*60*24),
        ('hr',        60*60),
        ('min',      60),
        ('sec',      1)
    ]

    strings=[]
    for period_name, period_seconds in periods:
        if seconds > period_seconds:
            period_value , seconds = divmod(seconds, period_seconds)
            has_s = 's' if period_value > 1 else ''
            strings.append("%s %s%s" % (period_value, period_name, has_s))

    return " ".join(strings)


def format_timedelta_to_HHMMSS(td):
    td_in_seconds = td.total_seconds()
    hours, remainder = divmod(td_in_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    if minutes < 10:
        minutes = "0{}".format(minutes)
    if seconds < 10:
        seconds = "0{}".format(seconds)
    return "{}:{}:{}".format(hours, minutes, seconds)


def weekly_totals(df):
    
    df['moving_time'] = pd.to_timedelta(df['moving_time'])
    dist = df.groupby(['grp_idx'])['distance'].sum().reset_index(name='distance')
    time = df.groupby(['grp_idx'])['moving_time'].sum().reset_index(name='time')
    time['time'] = time['time'].apply(lambda x: format_timedelta_to_HHMMSS(x))
    w_totals = pd.merge(dist, time, how='left', on='grp_idx')
    w_totals['wc'] = w_totals['grp_idx'].apply(lambda x: from_year_week_to_date(x).date())
    w_totals['distance'] = w_totals['distance'].map(lambda a: '{:.2f}'.format(a))
    return w_totals


def monthly_totals(df):

    df.index = pd.to_datetime(df['date'], format='%Y-%m-%d')
    df = df.drop(['id', 'date', 'type', 'grp_idx'], axis=1)
    monthly = df.groupby(by=[df.index.year, df.index.month]).sum()
    monthly['moving_time'] = monthly['moving_time'].apply(lambda x: format_timedelta_to_HHMMSS(x))
    monthly.index = monthly.index.set_names(['year', 'month'])
    monthly.reset_index(inplace=True)
    # use strptime to read date in specific format, then strftime to put it in desired format
    for i in range(len(monthly)):
        monthly.loc[i, 'month_start'] = datetime(year=monthly.loc[i, 'year'] ,month=monthly.loc[i, 'month'], day=1).date().strftime('%b-%Y')
    monthly['distance'] = monthly['distance'].map(lambda a: '{:.2f}'.format(a))
    return monthly


def annual_totals(df):

    df.index = pd.to_datetime(df['date'], format='%Y-%m-%d')
    df = df.drop(['id', 'date', 'type', 'grp_idx'], axis=1)
    annually = df.groupby(by=[df.index.year, df.index.month]).sum()
    annually['moving_time'] = annually['moving_time'].apply(lambda x: format_timedelta_to_HHMMSS(x))
    annually.index = annually.index.set_names(['year', 'month'])
    annually.reset_index(inplace=True)

    return annually


# Can use this to populate get_activity_ids, with high limits easily
# But will need to remove 'strava_app' for address to read/store jsons
# use_stored_data = True

# start_date =  datetime(2020, 1, 1).date()
# end_date = datetime(2020, 12, 31).date()

# access_token = get_access_token()
# athlete_id = get_athlete(access_token)['id']
# athlete_stats = get_athlete_stats(access_token, athlete_id, use_stored_data)
# total_activities  = total_activities = athlete_stats['all_ride_totals']['count'] + athlete_stats['all_run_totals']['count'] + athlete_stats['all_swim_totals']['count']
# activity_ids = get_activity_ids(access_token, total_activities, use_stored_data)
# runs = activity_ids[(activity_ids.type == 'Run')]
# monthly = monthly_totals(runs)
# print(monthly)