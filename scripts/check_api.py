import os
import requests
from dotenv import load_dotenv

load_dotenv()
token = os.environ["FOOTBALL_DATA_TOKEN"]

r = requests.get(
    "https://api.football-data.org/v4/competitions/PL/matches",
    headers={"X-Auth-Token": token},
    params={"status": "SCHEDULED"},
    timeout=30,
)
print("Status:", r.status_code)

# Show any rate-limit headers so we know how to throttle
for key, value in r.headers.items():
    if "request" in key.lower() or "limit" in key.lower():
        print(key, "=", value)

matches = r.json().get("matches", [])
print(len(matches), "upcoming Premier League matches")
if matches:
    m = matches[0]
    print(m["utcDate"], m["homeTeam"]["name"], "vs", m["awayTeam"]["name"])