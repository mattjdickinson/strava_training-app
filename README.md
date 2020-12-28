# Strava Training Log

## Project overview
This is a web app using Strava's API. My latest runs are pulled from Strava and presented in a traditional training log for running.  

From:


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

- Run the project using the command:

    `FLASK_APP=strava_app.webapp FLASK_ENV=development flask run --port 8080`

## How the project works

## Limitations

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


