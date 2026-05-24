import requests
import json

payload = {
    "operationName": "AnyPlayerLayoutQuery",
    "variables": {
        "slug": "bryan-heynen",
        "onlyPrimary": False
    },
    "extensions": {
        "operationId": "React/a809e5dae931764014e854f4ba174c338195ee3fe2cf12bc971687941c0fe40d"
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

with open("player_test.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("saved player_test.json")
