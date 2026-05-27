import os
import json
import time
import argparse
import requests
from datetime import datetime
from config import LEAGUES

SORARE_URL = "https://api.sorare.com/graphql"
PERFORMANCE_OPERATION_ID = "React/3ea98095326204593e8d89d7cf014fdf849f43b2b5534ce70047281efa62403e"


POSITION_MAP = {
    "Goalkeeper": "Goalkeeper",
    "Defender": "Defender",
    "Midfielder": "Midfielder",
    "Forward": "Forward"
}


def post_sorare(payload, label):
    for attempt in range(5):
        response = requests.post(
            SORARE_URL,
            json=payload,
            headers={"content-type": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                raise Exception(data["errors"])
            return data

        if response.status_code == 429:
            wait = 60 * (attempt + 1)
            print(f"Rate limit hit for {label}. Waiting {wait} seconds...")
            time.sleep(wait)
            continue

        raise Exception(f"HTTP {response.status_code}: {response.text[:300]}")

    raise Exception(f"Too many rate limits for {label}")


def get_stat_value(avg_block, stat_name):
    if not avg_block:
        return None

    for stat in avg_block.get("lastIndividualStats", []):
        if stat.get("stat") == stat_name:
            return stat.get("value")

    return None


def fetch_performance(player):
    slug = player["slug"]
    position = POSITION_MAP.get(player.get("position"), player.get("position", "Midfielder"))

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
    any_player = data.get("data", {}).get("anyPlayer", {}) or {}
    avg = any_player.get("anySo5AverageLastScore", {}) or {}

    games_started = get_stat_value(avg, "GAME_STARTED")
    starter_rate = round((games_started / 10) * 100, 1) if games_started is not None else None

    return {
        "slug": slug,
        "displayName": player.get("displayName"),
        "club": player.get("club"),
        "club_slug": player.get("club_slug"),
        "position": player.get("position"),
        "country": player.get("country"),
        "age": player.get("age"),
        "birthDay": player.get("birthDay"),
        "u23": player.get("u23"),

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


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--league", required=True, choices=LEAGUES.keys())
    parser.add_argument("--season", required=True, type=int)
    parser.add_argument("--snapshot", required=False, default="manual")

    args = parser.parse_args()

    league_key = args.league
    season = args.season
    snapshot_label = args.snapshot

    base_dir = f"data/{league_key}/{season}"
    player_data_file = f"{base_dir}/player_data.json"
    latest_file = f"{base_dir}/player_metrics_latest.json"
    snapshot_dir = f"{base_dir}/snapshots"
    snapshot_file = f"{snapshot_dir}/player_metrics_{snapshot_label}.json"

    os.makedirs(snapshot_dir, exist_ok=True)

    with open(player_data_file, "r", encoding="utf-8") as f:
        player_data = json.load(f)

    all_players = player_data["players"]

    OFFSET_PLAYERS = int(os.environ.get("OFFSET_PLAYERS", 0))
    LIMIT_PLAYERS = int(os.environ.get("LIMIT_PLAYERS", 150))

    players = all_players[OFFSET_PLAYERS:OFFSET_PLAYERS + LIMIT_PLAYERS]

    existing_by_slug = {}
    existing_errors = []

    if os.path.exists(latest_file):
        with open(latest_file, "r", encoding="utf-8") as f:
            existing = json.load(f)

        for item in existing.get("players", []):
            if item.get("slug"):
                existing_by_slug[item["slug"]] = item

        existing_errors = existing.get("errors", [])

        print(f"Existing metrics loaded: {len(existing_by_slug)}")

    print("League:", league_key)
    print("Season:", season)
    print("Snapshot:", snapshot_label)
    print("Total players:", len(all_players))
    print("Offset:", OFFSET_PLAYERS)
    print("Limit:", LIMIT_PLAYERS)
    print("Players in this run:", len(players))

    errors = existing_errors

    for i, player in enumerate(players, start=1):
        slug = player.get("slug")
        name = player.get("displayName", slug)

        if not slug:
            continue

        print(f"[{i}/{len(players)}] Updating metrics: {name}")

        try:
            metric = fetch_performance(player)
            existing_by_slug[slug] = metric

        except Exception as e:
            print("ERROR:", slug, str(e))
            errors.append({
                "slug": slug,
                "name": name,
                "error": str(e),
                "updated_at": datetime.utcnow().isoformat()
            })

        time.sleep(2)

    metrics = list(existing_by_slug.values())

    output = {
        "updated_at": datetime.utcnow().isoformat(),
        "league": player_data.get("league"),
        "league_key": league_key,
        "seasonStartYear": season,
        "snapshot": snapshot_label,
        "total_players": len(metrics),
        "total_errors": len(errors),
        "offset": OFFSET_PLAYERS,
        "limit": LIMIT_PLAYERS,
        "errors": errors,
        "players": metrics
    }

    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    with open(snapshot_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("==============================")
    print("DONE")
    print("Metrics saved:", len(metrics))
    print("Errors:", len(errors))
    print("Latest file:", latest_file)
    print("Snapshot file:", snapshot_file)
    print("==============================")


if __name__ == "__main__":
    main()
