import requests
import json

PLAYER_SLUG = "bryan-heynen"

payload = {
    "operationName": "PerformanceBlockQuery",
    "variables": {
        "slug": PLAYER_SLUG
    },
    "extensions": {
        "operationId": "PerformanceBlockQuery"
    }
}

print(f"Downloading performance data for {PLAYER_SLUG}")

r = requests.post(
    "https://api.sorare.com/graphql",
    json=payload,
    headers={
        "content-type": "application/json"
    }
)

print("STATUS:", r.status_code)

try:
    data = r.json()
except Exception as e:
    print("JSON ERROR:", e)
    print(r.text[:5000])
    raise

with open("performance_test.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Saved performance_test.json")


KEYWORDS = [
    "l5",
    "l10",
    "l15",
    "l40",
    "score",
    "scores",
    "average",
    "averageScore",
    "price",
    "valuation",
    "starter",
    "starting",
    "decisive",
    "aa",
    "game",
    "games",
    "performance"
]


def scan(obj, path="root"):

    if isinstance(obj, dict):

        for k, v in obj.items():

            current_path = f"{path}.{k}"

            if any(word.lower() in k.lower() for word in KEYWORDS):

                print("\n" + "=" * 100)
                print("FOUND:", current_path)

                try:
                    print(json.dumps(v, indent=2, ensure_ascii=False)[:5000])
                except:
                    print(v)

            scan(v, current_path)

    elif isinstance(obj, list):

        for i, item in enumerate(obj):
            scan(item, f"{path}[{i}]")


print("\nSTARTING SCAN")
scan(data)
print("\nSCAN COMPLETE")


print("\nFIRST 10000 CHARS OF RESPONSE")
print("=" * 100)

try:
    print(json.dumps(data, indent=2, ensure_ascii=False)[:10000])
except:
    pass
