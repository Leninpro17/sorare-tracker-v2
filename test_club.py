import requests
import json

payload = {
    "operationName": "FootballClubOverviewQuery",
    "variables": {
        "slug": "genk-genk",
        "seasonStartYear": 2025
    },
    "extensions": {
        "operationId": "React/a288341ac39d1684e9492982e6dbcf7369b005b3df0afff9eeceaa81430ecf5b"
    }
}

r = requests.post(
    "https://api.sorare.com/graphql",
    json=payload,
    headers={
        "content-type": "application/json"
    }
)

print(r.status_code)

try:
    data = r.json()

    with open("genk.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("saved genk.json")

except Exception as e:
    print(r.text)
    print(e)
