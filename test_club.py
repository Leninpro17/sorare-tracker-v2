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

print("STATUS:", r.status_code)

data = r.json()

with open("genk.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("saved genk.json")


def scan(obj):
    if isinstance(obj, dict):

        if obj.get("__typename") == "Player":
            print("\nPLAYER FOUND")
            print(json.dumps(obj, indent=2, ensure_ascii=False)[:3000])
            print("=" * 100)

        for v in obj.values():
            scan(v)

    elif isinstance(obj, list):
        for item in obj:
            scan(item)


scan(data)

import shutil

shutil.copy("genk.json", "docs/genk.json")
