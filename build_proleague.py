import os
import requests

API_KEY = os.environ["API_FOOTBALL_KEY"]

headers = {
    "x-apisports-key": API_KEY
}

response = requests.get(
    "https://v3.football.api-sports.io/leagues?search=Belgium",
    headers=headers
)

print(response.status_code)
print(response.text)
