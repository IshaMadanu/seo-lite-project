from flask import Flask, render_template
app = Flask(__name__)

@app.route("/")
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

    return render_template("route.html")


if __name__ == '__main__':
    app.run(debug=True)