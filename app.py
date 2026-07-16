import os
import json
from dotenv import load_dotenv
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session

load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-change-this') 

# #llm data
# DATA = os.path.join(os.path.dirname(__file___), 'data', 'nonprofits.json')
# with open(DATA) as f:
#     NONPROFITS = json.load(f)

#add user DB
MOCK_USERS = {
    "jane.doe@example.com": {"password": "password123", "name": "Jane Doe"}
}

def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get('user_email'):
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    return wrapped

@app.route("/", methods=['GET', 'POST'])
@app.route("/login", methods=['GET', 'POST'])

def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        pswd = request.form.get('password', '')

        #replace w check in DB
        user = MOCK_USERS.get(email)
        if user and user['password'] == pswd:
            session['user_email'] = email
            return redirect(url_for('profile'))
        error = "Invalid login"

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    email = session['user_email']
    mock_user = {
        "name": MOCK_USERS.get(email, {}).get("name", "Jane Doe"),
        "email": email,
        "avatar_url": None,
    }
    #get user from DB
    return render_template("profile.html", user=mock_user)

@app.route("/recommendations", methods=['GET', 'POST'])
@login_required
def recommendations():
    #call llm w buser pref from DB

    dummy_nonprofits = [
        {"name": " Nonprofit 1", "reason": "Matches: animals"},
        {"name": " Nonprofit 2", "reason": "Matches: environment"},
        {"name": " Nonprofit 3", "reason": "Matches: education"},
    ]

    return render_template("recommendations.html", nonprofits=dummy_nonprofits)

@app.route("/route", methods=['GET', 'POST'])
@login_required
def route():
    #googlemaps api for dir
    maps_key = os.environ.get("MAPS_API_KEY")


    return render_template("route.html", maps_api_key=maps_key)


if __name__ == '__main__':
    app.run(debug=True)