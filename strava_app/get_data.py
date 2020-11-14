import requests
import urllib3
import json
import os

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
refresh_token = os.environ.get('REFRESH_TOKEN')

# import sys, os
# sys.path.append('/Users/matt/Python/strava-training')

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

    # Refresh token obtained through authorisation code from read_all activities (different to strava default of 'read'). Refresh_token doens't change. See 'activity_readall.txt' for steps
    print("Requesting Token...\n")
    res = requests.post(auth_url, data=payload, verify=False)
    # print(res.json())
    access_token = res.json()['access_token']
    print("Access Token = {}\n".format(access_token))

    header = {'Authorization': 'Bearer ' + access_token}
    param = {'per_page': 200, 'page': 1}
    data = requests.get(activities_url, headers=header, params=param).json()

    # print(type(my_dataset)) # List of dicts (name, value pairs)
    # print(json.dumps(data, indent=2))

    # Get encoded polyline for use in google maps platform polyline
    # https://developers.google.com/maps/documentation/utilities/polylineutility

    # print(data[1]['map']['summary_polyline'])

    return data

data = get_dataset()
print(json.dumps(data[0], indent=2))
for activity in data:
    print(activity['name'])

