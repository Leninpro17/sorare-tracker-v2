import requests
import json

payload = {
    "operationName": "AnyPlayerLayoutQuery",
    "variables": {
        "onlyPrimary": False,
        "slug": "bryan-heynen"
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

with open("player_layout.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("saved player_layout.json")


KEYWORDS = [
    "birth",
    "age",
    "date",
    "u23"
]


def scan(obj, path="root"):

    if isinstance(obj, dict):

        for k, v in obj.items():

            current = f"{path}.{k}"

            if any(word in k.lower() for word in KEYWORDS):
                print("\n" + "=" * 80)
                print("FOUND:", current)
                print(json.dumps(v, indent=2, ensure_ascii=False)[:3000])

            scan(v, current)

    elif isinstance(obj, list):

        for i, item in enumerate(obj):
            scan(item, f"{path}[{i}]")


scan(data)
