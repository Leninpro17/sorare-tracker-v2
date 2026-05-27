import json

FILE = "data/belgium/2025/player_prices_latest.json"

with open(FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

players = data.get("players", [])

print("Total players:", len(players))

for player in players[:5]:
    print("\n==============================")
    print("Name:", player.get("displayName"))
    print("Slug:", player.get("slug"))
    print("Club:", player.get("club"))
    print("Position:", player.get("position"))

    print("\nLimited floor:")
    print(json.dumps(player.get("limitedFloor"), indent=2, ensure_ascii=False))

    print("\nRare floor:")
    print(json.dumps(player.get("rareFloor"), indent=2, ensure_ascii=False))
