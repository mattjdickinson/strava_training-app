import flask
app = flask.Flask(__name__)
app.static_folder = 'static'

# Running the app using debug=True allows the app to auto-update every time the code gets edited.
# Not sure this working 
if __name__ == "__main__":
    app.run(debug=True)