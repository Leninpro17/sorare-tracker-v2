import json
import time
import requests
from datetime import datetime

INPUT_FILE = "player_data.json"
OUTPUT_FILE = "player_metrics.json"

OPERATION_ID = "React/3ea98095326204593e8d89d7cf014fdf849f43b2b5534ce70047281efa62403e"

POSITION_MAP = {
    "Goalkeeper": "Goalkeeper",
    "Defender": "Defender",
    "Midfielder": "Midfielder",
    "Forward": "Forward",
    "GK": "Goalkeeper",
    "DEF": "Defender",
    "MID": "Midfielder",
    "FWD": "Forward"
}


def get_players():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "players" in data:
        return data["players"]

    if isinstance(data, dict):
        players = []
        for slug, info in data.items():
            info["slug"] = slug
            players.append(info)
        return players

    return data


def get_stat_value(avg_block, stat_name):
    if not avg_block:
        return None

    for stat in avg_block.get("lastIndividualStats", []):
        if stat.get("stat") == stat_name:
            return stat.get("value")

    return None


def fetch_metrics(player):
    slug = player.get("slug")
    position = POSITION_MAP.get(
        player.get("position"),
        player.get("position", "Midfielder")
    )

    payload = {
        "operationName": "PerformanceBlocksQuery",
        "variables": {
            "playerSlug": slug,
            "position": position,
            "span": "LAST_TEN"
        },
        "extensions": {
            "operationId": OPERATION_ID
        }
    }

    r = requests.post(
        "https://api.sorare.com/graphql",
        json=payload,
        headers={"content-type": "application/json"},
        timeout=30
    )

    if r.status_code == 429:
    print("Rate limit hit. Waiting 60 seconds...")
    time.sleep(60)
    return fetch_metrics(player)

if r.status_code != 200:
    raise Exception(f"HTTP {r.status_code}: {r.text[:200]}")

    data = r.json()

    any_player = data.get("data", {}).get("anyPlayer", {})

    avg = any_player.get("anySo5AverageLastScore", {})

    games_started = get_stat_value(avg, "GAME_STARTED")

    starter_rate = None
    if games_started is not None:
        starter_rate = round((games_started / 10) * 100, 1)

    return {
        "slug": slug,
        "displayName": player.get("displayName"),
        "club": player.get("club"),
        "club_slug": player.get("club_slug"),
        "position": player.get("position"),
        "country": player.get("country"),
        "l5": any_player.get("lastFiveSo5AverageScore"),
        "l10": any_player.get("lastTenPlayedSo5AverageScore"),
        "l40": any_player.get("lastFortySo5AverageScore"),
        "seasonAverage": any_player.get("seasonAverage"),
        "aa": avg.get("averageValueAllAround"),
        "decisive": avg.get("averageValueDecisive"),
        "total": avg.get("averageValueTotal"),
        "lastScores": avg.get("lastIndividualScores"),
        "minutesLast10": get_stat_value(avg, "MINS_PLAYED"),
        "gamesStartedLast10": games_started,
        "starterRate": starter_rate,
        "updated_at": datetime.utcnow().isoformat()
    }


players = get_players()

metrics = []
errors = []

print(f"Players to update: {len(players)}")

for i, player in enumerate(players, start=1):
    slug = player.get("slug")
    name = player.get("displayName", slug)

    if not slug:
        continue

    print(f"[{i}/{len(players)}] {name}")

    try:
        metrics.append(fetch_metrics(player))
    except Exception as e:
        print("ERROR:", slug, str(e))
        errors.append({
            "slug": slug,
            "error": str(e)
        })

    time.sleep(0.25)

output = {
    "updated_at": datetime.utcnow().isoformat(),
    "source": "Sorare PerformanceBlocksQuery",
    "total_players": len(metrics),
    "errors": errors,
    "players": metrics
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("==============================")
print("DONE")
print("Metrics saved:", len(metrics))
print("Errors:", len(errors))
print("File created:", OUTPUT_FILE)
print("==============================")
