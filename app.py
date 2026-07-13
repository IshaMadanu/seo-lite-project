import os
from flask import Flask, render_template
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

@app.route("/") # methods=['GET', 'POST']
@app.route("/login")

def login():
    return render_template('login.html', subtitle='Login Page')

@app.route("/profile")
def profile():
    #get user from DB
    return render_template("profile.html")

@app.route("/recommendations")
def recommendations():
    #call llm w buser pref from DB

    dummy_nonprofits = [
        {"name": " Nonprofit 1", "reason": "Matches: animals"},
        {"name": " Nonprofit 2", "reason": "Matches: environment"},
        {"name": " Nonprofit 3", "reason": "Matches: education"},
    ]

    return render_template("recommendations.html", nonprofits=dummy_nonprofits)

@app.route("/route")
def route():
    #googlemaps api for dir
    maps_key = os.environ.get("MAPS_API_KEY")


    return render_template("route.html", maps_api_key=maps_key)


if __name__ == '__main__':
    app.run(debug=True)