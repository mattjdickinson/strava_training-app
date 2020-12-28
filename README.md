# Strava Training Log

## Project overview
This is a web app using Strava's API. My latest runs are pulled from Strava and presented in a traditional training log for running.  

From:

![Strava](https://github.com/mattjdickinson/strava-training/blob/master/Screenshots/Screenshot%202020-12-28%20at%2012.55.23.png?raw=true) 

To:

![Training](https://github.com/mattjdickinson/strava-training/blob/master/Screenshots/Screenshot%202020-12-28%20at%2012.34.20.png?raw=true) 

The app includes mileage totals by weeky and monthly:

![Weekly](https://github.com/mattjdickinson/strava-training/blob/master/Screenshots/Screenshot%202020-12-28%20at%2012.51.07.png?raw=true) 

![Monthly](https://github.com/mattjdickinson/strava-training/blob/master/Screenshots/Screenshot%202020-12-28%20at%2012.51.22.png?raw=true) 

## How to run
- Set up your environment and activate: 

    `source env/bin/activate`

- Install the required packages using the command:

    `pip install -r requirements.txt`

- Make sure to change directory appropriately:

    `cd /Users/matt/Python/strava-training`

- To run your own data you will need to set environment variables for your CLIENT_ID, SECRET_KEY, REFRESH_TOKEN.  This requires a few steps. In the first part, I followed steps in this video https://youtu.be/sgscChKfGyg. The steps are oultined below. I used Postman the the GET and POST requests.

    1. Set up an app application on your Strava Account to get your CLIENT_ID.
    
    2. Use the CLIENT_ID in the url below to get your one-time authorisation code from authorisation page. This is a one time, manual step. Paste the below code in a browser, hit enter, then grab the "code" part from the resulting url. Note will look like it failed but we're just interested in the code in the url. DOn't include '[]' when copying in CLIENT_ID.

        https://www.strava.com/oauth/authorize?client_id=[CLIENT_ID]&redirect_uri=http://localhost&response_type=code&scope=activity:read_all

    2. Exchange the authorisation code, obtained in the previous step, for access token & refresh token using the POST request, replaying [] names are appropriate

        https://www.strava.com/oauth/token?client_id=[CLIENT_ID]&client_secret=[CLIENT_SECRET]&code=[AUTHORIZATION_CODE]&grant_type=authorization_code


    3. View your activiies using the access token just received using the GET request:

        https://www.strava.com/api/v3/athlete/activities?access_token=[ACCESS_TOKEN]

    4. Use refresh token to get new access tokens POST requests. Note this step is performed in the app since the  app will need to check if the accesstoken has expired and if so refresh it with refresh token:
    
        https://www.strava.com/oauth/token?client_id=[CLIENT_ID]client_secret=[CLIENT_SECRET]&refresh_token=[REFRESH_TOKEN]&grant_type=refresh_token

    5. See https://www.youtube.com/watch?v=5iWhQWVXosU for steps on how to do this. For mac users, the newer osx version uses zsh instead of bash, so using .bash_profile doesn't work, instead enter "nano .zshrc" in the terminal, and then add in the variables:

    export CLIENT_ID="xxx"
    export CLIENT_SECRET="xxx"
    export REFRESH_TOKEN="xxx"

- Run the project using the command:

    `FLASK_APP=strava_app.webapp FLASK_ENV=development flask run --port 8080`

## Limitations

## How the project works


## Future Planned features

- Add time as secondary axis to weekly and monthly charts
- Add monthly totals to activity breakdown table
- Add in OAuth so user users can use the app
- Add database with user login and password so to store data.
- Add in mechanism to pull all activities into databse overtime to get around API limits.
- Refresh data to check if activity data exists in database and to only pull new data, thus limiting API calls.
- Add date ranges throughout for user input
- Allow user to export data to Excel / Google Sheets
- Better stlying on the web page
- Add visual page 'downloading activity number x out of y' 
- Use past data to predict future performance? Could do something simple based on past race performance, and Jack Daniels formula
- Link to show map of activity (individual GET request, polyline graph)
- Map heatspot based on speed


