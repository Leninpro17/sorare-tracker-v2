import os
import json
import time
import argparse
import requests
from datetime import datetime
from config import LEAGUES

SORARE_URL = "https://api.sorare.com/graphql"

CLUB_OPERATION_ID = "React/a288341ac39d1684e9492982e6dbcf7369b005b3df0afff9eeceaa81430ecf5b"
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


def load_club_list(league_key, season_start_year):
    file_path = f"data/{league_key}/{season_start_year}/club_list.json"

    if not os.path.exists(file_path):
        raise Exception(f"club_list.json non trovato: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f), file_path


def fetch_club(club_slug, season_start_year):
    payload = {
        "operationName": "FootballClubOverviewQuery",
        "variables": {
            "slug": club_slug,
            "seasonStartYear": season_start_year
        },
        "extensions": {
            "operationId": CLUB_OPERATION_ID
        }
    }

    data = post_sorare(payload, club_slug)
    club = data["data"]["football"]["club"]

    if not club:
        raise Exception(f"Club non trovato: {club_slug}")

    return club


def fetch_player_layout(player_slug):
    payload = {
        "operationName": "AnyPlayerLayoutQuery",
        "variables": {
            "onlyPrimary": False,
            "slug": player_slug
        },
        "extensions": {
            "operationId": LAYOUT_OPERATION_ID
        }
    }

    data = post_sorare(payload, player_slug)
    return data.get("data", {}).get("anyPlayer", {}) or {}


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--league",
        required=True,
        choices=LEAGUES.keys(),
        help="Liga da aggiornare"
    )

    parser.add_argument(
        "--season",
        required=True,
        type=int,
        help="Anno inizio stagione. Esempio: 2025 per stagione 2025/26"
    )

    args = parser.parse_args()

    league_key = args.league
    season_start_year = args.season

    league_config = LEAGUES[league_key]
    league_name = league_config["name"]

    club_list, club_list_file = load_club_list(
        league_key,
        season_start_year
    )

    output_dir = f"data/{league_key}/{season_start_year}"
    os.makedirs(output_dir, exist_ok=True)

    output_file = f"{output_dir}/player_data.json"

    clubs = club_list.get("clubs", [])

    if not clubs:
        raise Exception(f"Nessun club trovato in {club_list_file}")

    players_by_slug = {}
    errors = []

    print("Club list:", club_list_file)
    print("League:", league_name)
    print("Season:", season_start_year)
    print("Clubs:", len(clubs))

    for club_index, club_info in enumerate(clubs, start=1):
        club_slug = club_info["slug"]

        print(f"\n[{club_index}/{len(clubs)}] Scanning club: {club_slug}")

        try:
            club = fetch_club(
                club_slug,
                season_start_year
            )

            club_name = club["name"]
            memberships = club["activeMemberships"]["nodes"]

            print(f"Club: {club_name} | Players: {len(memberships)}")

            for membership in memberships:
                player = membership.get("player")

                if not player:
                    continue

                player_slug = player.get("slug")

                if not player_slug:
                    continue

                layout = fetch_player_layout(player_slug)

                players_by_slug[player_slug] = {
                    "slug": player_slug,
                    "displayName": player.get("displayName"),
                    "club": club_name,
                    "club_slug": club_slug,
                    "position": player.get("position"),
                    "country": (
                        player.get("country", {}).get("name")
                        if player.get("country")
                        else None
                    ),
                    "age": layout.get("age"),
                    "birthDay": layout.get("birthDay"),
                    "u23": layout.get("u23Eligible"),
                    "avatarPictureUrl": player.get("avatarPictureUrl"),
                    "membershipStartDate": membership.get("startDate")
                }

                time.sleep(0.7)

        except Exception as e:
            print("ERROR CLUB:", club_slug, str(e))
            errors.append({
                "club_slug": club_slug,
                "error": str(e)
            })

    players = list(players_by_slug.values())

    if not players:
        raise Exception("Nessun giocatore trovato. Controlla club_list o query Sorare.")

    output = {
        "updated_at": datetime.utcnow().isoformat(),
        "league": league_name,
        "league_key": league_key,
        "seasonStartYear": season_start_year,
        "total_clubs": len(clubs),
        "total_players": len(players),
        "errors": errors,
        "players": players
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("\n==============================")
    print("DONE")
    print("League:", league_name)
    print("Season:", season_start_year)
    print("Players saved:", len(players))
    print("Errors:", len(errors))
    print("File created:", output_file)
    print("==============================")


if __name__ == "__main__":
    main()
