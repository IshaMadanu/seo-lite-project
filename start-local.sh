#!/usr/bin/env sh
# Start DynamoDB Local + the Flask app for local development.
set -e
cd "$(dirname "$0")"

echo "Starting DynamoDB Local (docker)..."
docker compose up -d

printf "Waiting for DynamoDB Local"
until curl -s -o /dev/null http://localhost:8000; do
  printf "."
  sleep 1
done
echo " ready."

if [ ! -d venv ]; then
  echo "Creating virtualenv..."
  python3 -m venv venv
fi
./venv/bin/pip install -q -r requirements.txt

# default to 5057: macOS AirPlay Receiver squats on port 5000
PORT="${PORT:-5057}"
echo "Starting app on http://127.0.0.1:$PORT"
exec ./venv/bin/python -m flask --app 'app:create_app()' run --port "$PORT"
