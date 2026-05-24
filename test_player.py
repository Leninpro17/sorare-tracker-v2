import requests
import json

PLAYER_SLUG = "bryan-heynen"

payload = {
    "operationName": "PerformanceBlocksQuery",
    "variables": {
        "playerSlug": PLAYER_SLUG,
        "position": "Midfielder",
        "span": "LAST_TEN"
    },
    "extensions": {
        "operationId": "React/3ea98095326204593e8d89d7cf014fdf849f43b2b5534ce70047281efa62403e"
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
except Exception:
    print(r.text)
    raise

with open("performance_test.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Saved performance_test.json")


KEYWORDS = [
    "score",
    "scores",
    "average",
    "averageScore",
    "l10",
    "l40",
    "percentile",
    "starter",
    "decisive",
    "allaround",
    "aa",
    "performance",
    "rank",
    "price",
    "valuation"
    "age"
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
