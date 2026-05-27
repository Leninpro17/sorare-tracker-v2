import os
import json
import time
import argparse
import requests
from datetime import datetime
from config import LEAGUES

SORARE_URL = "https://api.sorare.com/graphql"

LAYOUT_OPERATION_ID = "React/a809e5dae931764014e854f4ba174c338195ee3fe2cf12bc971687941c0fe40d"


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


def cents_to_unit(value):
    if value is None:
        return None

    return round(value / 100, 2)


def wei_to_eth(value):
    if value is None:
        return None

    try:
        return float(value) / 10**18
    except Exception:
        return None


def get_amounts(card):
    if not card:
        return {
            "eur": None,
            "usd": None,
            "eth": None,
            "referenceCurrency": None
        }

    offer = card.get("liveSingleSaleOffer")

    if not offer:
        return {
            "eur": None,
            "usd": None,
            "eth": None,
            "referenceCurrency": None
        }

    amounts = (
        offer.get("receiverSide", {})
        .get("amounts", {})
    )

    return {
        "eur": cents_to_unit(amounts.get("eurCents")),
        "usd": cents_to_unit(amounts.get("usdCents")),
        "eth": wei_to_eth(amounts.get("wei")),
        "referenceCurrency": amounts.get("referenceCurrency")
    }


def floor_type(card, season):
    if not card:
        return None

    season_year = card.get("seasonYear")

    if season_year is None:
        return None

    if int(season_year) >= int(season):
        return "IN_SEASON"

    return "CLASSIC"


def extract_card_floor(any_player, field_name, season):
    card = any_player.get(field_name)

    amounts = get_amounts(card)

    if not card:
        return {
            "eur": None,
            "usd": None,
            "eth": None,
            "referenceCurrency": None,
            "seasonYear": None,
            "type": None,
            "cardSlug": None,
            "offerEndDate": None
        }

    offer = card.get("liveSingleSaleOffer")

    return {
        "eur": amounts["eur"],
        "usd": amounts["usd"],
        "eth": amounts["eth"],
        "referenceCurrency": amounts["referenceCurrency"],
        "seasonYear": card.get("seasonYear"),
        "type": floor_type(card, season),
        "cardSlug": card.get("slug"),
        "offerEndDate": offer.get("endDate") if offer else None
    }


def fetch_prices(player, season):
    slug = player["slug"]

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
    any_player = data.get("data", {}).get("anyPlayer", {}) or {}

    return {
        "slug": slug,
        "displayName": player.get("displayName"),
        "club": player.get("club"),
        "club_slug": player.get("club_slug"),
        "position": player.get("position"),
        "age": player.get("age"),
        "u23": player.get("u23"),

        "limitedFloor": extract_card_floor(
            any_player,
            "lowestPriceLimitedCard",
            season
        ),
        "rareFloor": extract_card_floor(
            any_player,
            "lowestPriceRareCard",
            season
        ),
        "superRareFloor": extract_card_floor(
            any_player,
            "lowestPriceSuperRareCard",
            season
        ),
        "uniqueFloor": extract_card_floor(
            any_player,
            "lowestPriceUniqueCard",
            season
        ),

        "updated_at": datetime.utcnow().isoformat()
    }


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--league",
        required=True,
        choices=LEAGUES.keys()
    )

    parser.add_argument(
        "--season",
        required=True,
        type=int
    )

    parser.add_argument(
        "--snapshot",
        required=False,
        default="manual"
    )

    args = parser.parse_args()

    league_key = args.league
    season = args.season
    snapshot_label = args.snapshot

    base_dir = f"data/{league_key}/{season}"
    player_data_file = f"{base_dir}/player_data.json"

    latest_file = f"{base_dir}/player_prices_latest.json"

    snapshot_dir = f"{base_dir}/snapshots"
    snapshot_file = f"{snapshot_dir}/player_prices_{snapshot_label}.json"

    os.makedirs(snapshot_dir, exist_ok=True)

    if not os.path.exists(player_data_file):
        raise Exception(f"player_data.json non trovato: {player_data_file}")

    with open(player_data_file, "r", encoding="utf-8") as f:
        player_data = json.load(f)

    all_players = player_data["players"]

    OFFSET_PLAYERS = int(os.environ.get("OFFSET_PLAYERS", 0))
    LIMIT_PLAYERS = int(os.environ.get("LIMIT_PLAYERS", 150))

    players = all_players[OFFSET_PLAYERS:OFFSET_PLAYERS + LIMIT_PLAYERS]

    existing_by_slug = {}
    existing_errors = []

    if os.path.exists(latest_file):
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                existing = json.load(f)

            for item in existing.get("players", []):
                if item.get("slug"):
                    existing_by_slug[item["slug"]] = item

            existing_errors = existing.get("errors", [])

            print(f"Existing prices loaded: {len(existing_by_slug)}")

        except Exception as e:
            print("Could not load existing prices:", str(e))

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

        print(f"[{i}/{len(players)}] Updating prices: {name}")

        try:
            price_data = fetch_prices(player, season)
            existing_by_slug[slug] = price_data

        except Exception as e:
            print("ERROR:", slug, str(e))
            errors.append({
                "slug": slug,
                "name": name,
                "error": str(e),
                "updated_at": datetime.utcnow().isoformat()
            })

        time.sleep(2)

    prices = list(existing_by_slug.values())

    output = {
        "updated_at": datetime.utcnow().isoformat(),
        "source": "Sorare AnyPlayerLayoutQuery",
        "league": player_data.get("league"),
        "league_key": league_key,
        "seasonStartYear": season,
        "snapshot": snapshot_label,
        "total_players": len(prices),
        "total_errors": len(errors),
        "offset": OFFSET_PLAYERS,
        "limit": LIMIT_PLAYERS,
        "errors": errors,
        "players": prices
    }

    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    with open(snapshot_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("==============================")
    print("DONE")
    print("Prices saved:", len(prices))
    print("Errors:", len(errors))
    print("Latest file:", latest_file)
    print("Snapshot file:", snapshot_file)
    print("==============================")


if __name__ == "__main__":
    main()
