import os
import json
import time
import requests
from datetime import datetime

INPUT_FILE = "player_data.json"
OUTPUT_FILE = "player_metrics.json"

PERFORMANCE_OPERATION_ID = "React/3ea98095326204593e8d89d7cf014fdf849f43b2b5534ce70047281efa62403e"
LAYOUT_OPERATION_ID = "React/a809e5dae931764014e854f4ba174c338195ee3fe2cf12bc971687941c0fe40d"

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


def post_sorare(payload, slug):
    for attempt in range(5):
        response = requests.post(
            "https://api.sorare.com/graphql",
            json=payload,
            headers={"content-type": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            return response.json()

        if response.status_code == 429:
            wait = 60 * (attempt + 1)
            print(f"Rate limit hit for {slug}. Waiting {wait} seconds...")
            time.sleep(wait)
            continue

        raise Exception(f"HTTP {response.status_code}: {response.text[:300]}")

    raise Exception(f"Too many rate limits for {slug}")


def get_players():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data["players"] if isinstance(data, dict) and "players" in data else data


def get_stat_value(avg_block, stat_name):
    if not avg_block:
        return None

    for stat in avg_block.get("lastIndividualStats", []):
        if stat.get("stat") == stat_name:
            return stat.get("value")

    return None


def fetch_layout(slug):
    payload = {
        "operationName": "AnyPlayerLayoutQuery",
        "variables": {
            "onlyPrimary": False,
            "slug": slug
        },
        "extensions": {
            "operationId": LAYOUT_OPERATION_ID
        }
    }

    data = post_sorare(payload, slug)
    return data.get("data", {}).get("anyPlayer", {}) or {}


def fetch_performance(player):
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
            "operationId": PERFORMANCE_OPERATION_ID
        }
    }

    data = post_sorare(payload, slug)
    return data.get("data", {}).get("anyPlayer", {}) or {}


def fetch_metrics(player):
    slug = player.get("slug")

    layout = fetch_layout(slug)
    performance = fetch_performance(player)

    avg = performance.get("anySo5AverageLastScore", {})

    games_started = get_stat_value(avg, "GAME_STARTED")
    starter_rate = round((games_started / 10) * 100, 1) if games_started is not None else None

    return {
        "slug": slug,
        "displayName": player.get("displayName"),
        "club": player.get("club"),
        "club_slug": player.get("club_slug"),
        "position": player.get("position"),
        "country": player.get("country"),

        "age": layout.get("age"),
        "birthDay": layout.get("birthDay"),
        "u23": layout.get("u23Eligible"),

        "l5": performance.get("lastFiveSo5AverageScore"),
        "l10": performance.get("lastTenPlayedSo5AverageScore"),
        "l40": performance.get("lastFortySo5AverageScore"),
        "seasonAverage": performance.get("seasonAverage"),

        "aa": avg.get("averageValueAllAround"),
        "decisive": avg.get("averageValueDecisive"),
        "total": avg.get("averageValueTotal"),
        "lastScores": avg.get("lastIndividualScores"),

        "minutesLast10": get_stat_value(avg, "MINS_PLAYED"),
        "gamesStartedLast10": games_started,
        "starterRate": starter_rate,

        "updated_at": datetime.utcnow().isoformat()
    }


all_players = get_players()

OFFSET_PLAYERS = int(os.environ.get("OFFSET_PLAYERS", 0))
LIMIT_PLAYERS = int(os.environ.get("LIMIT_PLAYERS", 150))

players = all_players[OFFSET_PLAYERS:OFFSET_PLAYERS + LIMIT_PLAYERS]

print(f"Total players: {len(all_players)}")
print(f"Offset: {OFFSET_PLAYERS}")
print(f"Limit: {LIMIT_PLAYERS}")
print(f"Players in this run: {len(players)}")
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
            "name": name,
            "error": str(e)
        })

    time.sleep(3)

output = {
    "updated_at": datetime.utcnow().isoformat(),
    "source": "Sorare Layout + PerformanceBlocksQuery",
    "total_players": len(metrics),
    "total_errors": len(errors),
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
