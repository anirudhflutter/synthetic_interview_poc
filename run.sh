#!/usr/bin/env bash
set -euo pipefail
# 1) Create & activate virtualenv (if not already)
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

# 2) Install deps
pip3 install --upgrade pip
pip3 install -r requirements.txt

echo "OpenAI SDK version via pip:"
pip3 show openai | grep Version

# 3) Ensure .env is present
if [ ! -f .env ]; then
  echo "Please copy .env.example to .env and fill in your keys."
  exit 1
fi

if lsof -i tcp:5000 &>/dev/null; then
  echo "Port 5000 in use, killing the process…"
  lsof -ti tcp:5000 | xargs kill -9 || true
fi

# 4) Start Flask API in background
echo "Starting Flask API on :5000…"
FLASK_APP=api.py flask run --port 5000 &

# 5) Give it a moment
sleep 2

# 6) Run a quick smoke call
echo "Testing /run-interview endpoint…"
curl -s -X POST http://127.0.0.1:5000/run-interview \
  -H 'Content-Type: application/json' \
  -d '{"questions":["What matters to you in a lifestyle brand?","How do you evaluate sustainability?"]}' \
  | jq .

# 7) Tail the logs so the demo stays alive
echo "Demo up—press Ctrl+C to stop."
wait
