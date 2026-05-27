import json
import requests

SORARE_URL = "https://api.sorare.com/graphql"

PLAYER_SLUG = "bryan-heynen"

LAYOUT_OPERATION_ID = "React/a809e5dae931764014e854f4ba174c338195ee3fe2cf12bc971687941c0fe40d"

payload = {
    "operationName": "AnyPlayerLayoutQuery",
    "variables": {
        "onlyPrimary": False,
        "slug": PLAYER_SLUG
    },
    "extensions": {
        "operationId": LAYOUT_OPERATION_ID
    }
}

r = requests.post(
    SORARE_URL,
    json=payload,
    headers={"content-type": "application/json"},
    timeout=30
)

print("STATUS:", r.status_code)

data = r.json()

with open("price_test.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Saved price_test.json")


KEYWORDS = [
    "lowestprice",
    "limited",
    "rare",
    "superrare",
    "unique",
    "season",
    "inseason",
    "classic",
    "cardedition",
    "amounts",
    "usdcents",
    "eurcents",
    "wei",
    "offer",
    "price",
    "floor"
]


def scan(obj, path="root"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            current = f"{path}.{k}"

            if any(word in k.lower() for word in KEYWORDS):
                print("\n" + "=" * 100)
                print("FOUND:", current)
                try:
                    print(json.dumps(v, indent=2, ensure_ascii=False)[:5000])
                except Exception:
                    print(v)

            scan(v, current)

    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            scan(item, f"{path}[{i}]")


scan(data)
