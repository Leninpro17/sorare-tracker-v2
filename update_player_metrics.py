import json
import time
import requests
from datetime import datetime, date

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

    return data


def get_stat_value(avg_block, stat_name):
    if not avg_block:
        return None

    for stat in avg_block.get("lastIndividualStats", []):
        if stat.get("stat") == stat_name:
            return stat.get("value")

    return None


def calculate_age(birth_date):
    if not birth_date:
        return None

    try:
        born = datetime.fromisoformat(birth_date[:10]).date()
        today = date.today()
        return today.year - born.year - (
            (today.month, today.day) < (born.month, born.day)
        )
    except Exception:
        return None


def fetch_metrics(player):
    slug = player.get("slug")
    position = POSITION_MAP.get(player.get("position"), player.get("position", "Midfielder"))

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

    for attempt in range(5):
        response = requests.post(
            "https://api.sorare.com/graphql",
            json=payload,
            headers={"content-type": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            break

        if response.status_code == 429:
            wait = 60 * (attempt + 1)
            print(f"Rate limit hit for {slug}. Waiting {wait} seconds...")
            time.sleep(wait)
            continue

        raise Exception(f"HTTP {response.status_code}: {response.text[:300]}")
    else:
        raise Exception(f"Too many rate limits for {slug}")

    data = response.json()
    any_player = data.get("data", {}).get("anyPlayer", {})
    avg = any_player.get("anySo5AverageLastScore", {})

    birth_date = any_player.get("birthDate") or any_player.get("birthdate")
    age = calculate_age(birth_date)

    games_started = get_stat_value(avg, "GAME_STARTED")
    starter_rate = round((games_started / 10) * 100, 1) if games_started is not None else None

    return {
        "slug": slug,
        "displayName": player.get("displayName"),
        "club": player.get("club"),
        "club_slug": player.get("club_slug"),
        "position": player.get("position"),
        "country": player.get("country"),

        "birthDate": birth_date,
        "age": age,
        "u23": age is not None and age <= 23,

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
        errors.append({"slug": slug, "name": name, "error": str(e)})

    time.sleep(2)

output = {
    "updated_at": datetime.utcnow().isoformat(),
    "source": "Sorare PerformanceBlocksQuery",
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
