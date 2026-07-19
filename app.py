import os
from dotenv import load_dotenv
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session

import dynamo

load_dotenv()

INTEREST_OPTIONS = ["animals", "environment", "education"]

# seeded so the test login on the login page keeps working
TEST_USER = {
    "email": "jane.doe@example.com",
    "password": "password123",
    "name": "Jane Doe",
}


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get('user_email'):
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    return wrapped


def create_app(resource=None):
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-change-this')

    db = dynamo.create_tables(resource)
    app.config['DYNAMO'] = db
    dynamo.create_user(
        db, TEST_USER["email"], TEST_USER["password"], name=TEST_USER["name"]
    )

    @app.route("/", methods=['GET', 'POST'])
    @app.route("/login", methods=['GET', 'POST'])
    def login():
        error = None
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            pswd = request.form.get('password', '')

            if dynamo.verify_user(db, email, pswd):
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

        saved = None
        if request.method == 'POST':
            selected = [
                i for i in request.form.getlist('interest')
                if i in INTEREST_OPTIONS
            ]
            dynamo.set_interests(db, email, selected)
            saved = True

        record = dynamo.get_user(db, email) or {}
        user = {
            "name": record.get("name", email),
            "email": email,
            "avatar_url": None,
        }
        return render_template(
            "profile.html",
            user=user,
            options=INTEREST_OPTIONS,
            interests=dynamo.get_interests(db, email),
            saved=saved,
        )

    @app.route("/recommendations", methods=['GET', 'POST'])
    @login_required
    def recommendations():
        interests = dynamo.get_interests(db, session['user_email'])

        # placeholder until the LLM call: one dummy nonprofit per saved interest
        nonprofits = [
            {"name": f"Nonprofit {n}", "reason": f"Matches: {interest}"}
            for n, interest in enumerate(interests, start=1)
        ]

        return render_template(
            "recommendations.html", nonprofits=nonprofits, interests=interests
        )

    @app.route("/route", methods=['GET', 'POST'])
    @login_required
    def route():
        #googlemaps api for dir
        maps_key = os.environ.get("MAPS_API_KEY")

        return render_template("route.html", maps_api_key=maps_key)

    return app


if __name__ == '__main__':
    create_app().run(debug=True)
