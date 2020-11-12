import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_dataset():

    auth_url = "https://www.strava.com/oauth/token"
    activities_url = "https://www.strava.com/api/v3/athlete/activities"

    payload = {
        'client_id': "55362",
        'client_secret': 'ce6ff8b1b337d045cd05e68e038f716a050d1ef9',
        'refresh_token': 'aa8407ef4cb66a2ef8c7bc685dc64d9debbd8af4',
        'grant_type': "refresh_token",
        'f': 'json'
    }

    # Refresh toen obtained through authorisation code from read_all activities (different to strava default of 'read'). Refresh_token doens't change. See 'activity_readall.txt' for steps
    print("Requesting Token...\n")
    res = requests.post(auth_url, data=payload, verify=False)
    # print(res.json())
    access_token = res.json()['access_token']
    print("Access Token = {}\n".format(access_token))

    header = {'Authorization': 'Bearer ' + access_token}
    param = {'per_page': 200, 'page': 1}
    my_dataset = requests.get(activities_url, headers=header, params=param).json()

    # print(type(my_dataset)) # List of dicts (name, value pairs)
    # print(my_dataset)
    print(my_dataset[1]['name'])

    # Get encoded polyline for use in google maps platform polyline
    # https://developers.google.com/maps/documentation/utilities/polylineutility

    print(my_dataset[1]['map']['summary_polyline'])

    return my_dataset


