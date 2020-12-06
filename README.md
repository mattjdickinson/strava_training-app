Put json into pandas df?
Put json into sqllite database so can query tables, present data, add description column that user can amend i.e. splits?
Both would allow filtering to be done easier


WHat do I want my table to show?
Name, start_date, distance, time, avg pace, lap splits (lap_id,time, distance, avg pace), avg lap split (useful for workouts 400m reps etc), suffer_score, AVG HR (if has_Hr = true), 
Lap splits will have to be some form of embedded list / tuple within the one item
Lap splits might be separate GET reuqest, using our activities
Allow user to specify date range
By default just do past year (or even past week) so that it runs quickly initially. This means we can keep initial GETs to one or two pages

TODO
Get basic table working for one activities
Extend table for all activities - loop alreayd in place for json, but will need to amend if use df
Add in week/month/year subtotals - split by activity type (run, ride) and don't show if not present i.e. if toggles
Add in date range to present results
Add in user filter i.e. run / workout type - or just fovcus on running for now
Export to Excel & google sheets
Add visual page 'downloading activity number x' when loading df and splits, since could take long time depending on number of activities
Style web page

Desirable
Add in week start (Mon / Sun)
Add in user description to activity - no as we won't be storing user data
Use past data to predict future performance? Could do something simple based on past race performance, and Jack Daniels formula
Link to show map of activity (individual GET request, polyline graph)
Map heatspot based on speed
DATE range specified in web browser to print from. default could be one year. Would need to amend functions


