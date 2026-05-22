import os
import requests
import json

API_KEY = os.environ["API_FOOTBALL_KEY"]

headers = {
    "x-apisports-key": API_KEY
}

response = requests.get(
    "https://v3.football.api-sports.io/teams?league=144&season=2025",
    headers=headers
)

print(response.status_code)

data = response.json()

print("Teams found:", len(data["response"]))

for team in data["response"]:
    print(
        team["team"]["id"],
        team["team"]["name"]
    )
