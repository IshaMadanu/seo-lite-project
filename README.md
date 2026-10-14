# VolunteerMatch

VolunteerMatch is a student-built web app that helps people discover New York City nonprofits based on causes they care about and compare lower-emission ways to get there.

## What it does

- Sign in to a demo account and view a personal profile.
- Choose interests in animals, the environment, and education.
- Get up to five nonprofit recommendations matched to those interests.
- Enter a starting address and compare walking, biking, driving, and public-transit routes on a map.
- See estimated travel times and CO₂ emissions, then record the estimated emissions saved by choosing a lower-emission route.

The nonprofit list is a bundled dataset of up to 100 New York City nonprofits ranked by revenue. The dataset-building script documents its source and filtering process.

## Tech stack

- **Backend:** Python, Flask, Jinja2
- **Database:** Amazon DynamoDB via boto3; DynamoDB Local for development
- **Maps and directions:** Google Maps JavaScript API and Directions service
- **Frontend:** HTML, CSS, and JavaScript
- **Testing:** pytest and Moto (mock AWS services)

## Run locally

### Prerequisites

- Python 3.10 or newer
- Docker Desktop (to run DynamoDB Local)
- A Google Maps API key to use the interactive map and directions

### Windows (PowerShell)

From the repository folder:

```powershell
docker compose up -d
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create a `.env` file in the repository root for local settings:

```dotenv
SECRET_KEY=replace-this-with-a-random-local-secret
DYNAMODB_ENDPOINT=http://localhost:8000
MAPS_API_KEY=your-google-maps-api-key
```

Enable the Google Maps JavaScript API and Directions API for your Google Cloud project. Add your API key to `.env` to load the map and calculate routes. Keep the key private and do not commit `.env`.

Start the app:

```powershell
python -m flask --app "app:create_app()" run --debug --port 5057
```

Open <http://127.0.0.1:5057> in your browser. Use the demo credentials shown on the login page:

```text
Email:    jane.doe@example.com
Password: password123
```

The app connects to DynamoDB Local at `http://localhost:8000` by default and creates its tables and demo data when it starts. You can change the endpoint with `DYNAMODB_ENDPOINT`. Without a Google Maps API key, you can use the profile and recommendation pages, but the map and route lookup will not work.

### macOS and Linux

Start DynamoDB Local, create and activate a virtual environment, install dependencies, then run Flask:

```bash
docker compose up -d
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python -m flask --app 'app:create_app()' run --debug --port 5057
```

Set the same values in a root-level `.env` file before starting the app. Alternatively, `./start-local.sh` starts DynamoDB Local, prepares the environment, installs dependencies, and launches the app on port 5057.

## Run the tests

With the project dependencies installed and the virtual environment activated:

```bash
pytest
```

The tests use Moto to mock DynamoDB, so they do not require the local database container or AWS credentials.

## Project structure

```text
app.py                    Flask routes and application setup
dynamo.py                 DynamoDB access and data helpers
data/nonprofits.json      Bundled nonprofit recommendation data
scripts/build_nonprofits.py
                          Script for building the nonprofit dataset from IRS data
templates/                Jinja HTML pages
static/style.css          Application styles
tests/                    Application and frontend tests
docker-compose.yml        DynamoDB Local service
```

## Notes

- The included login is intended for local demonstration only. Do not use the demo credentials or development secret in a deployed application.
- Google Maps may require a billing-enabled Google Cloud project. Restrict API keys to the APIs and websites that need them.
- The route emissions are estimates based on per-mile factors; they are for comparison and are not measured emissions.
