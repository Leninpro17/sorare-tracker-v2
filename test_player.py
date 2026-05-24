import requests
import json

PLAYER_SLUG = "bryan-heynen"

payload = {
    "operationName": "AnyPlayerLayoutQuery",
    "variables": {
        "slug": PLAYER_SLUG,
        "onlyPrimary": False
    },
    "extensions": {
        "operationId": "React/a809e5dae931764014e854f4ba174c338195ee3fe2cf12bc971687941c0fe40d"
    }
}

print(f"Downloading data for {PLAYER_SLUG}")

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

print("Saved player_test.json")


def scan(obj, path=""):
    if isinstance(obj, dict):

        for k, v in obj.items():

            current_path = f"{path}.{k}" if path else k

            keywords = [
                "score",
                "scores",
                "average",
                "l5",
                "l10",
                "l15",
                "l40",
                "game",
                "stat",
                "recent",
                "last"
            ]

            if any(word in k.lower() for word in keywords):
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
