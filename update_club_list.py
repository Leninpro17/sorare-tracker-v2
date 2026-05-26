import os
import json
import argparse
import requests
from datetime import datetime
from config import LEAGUES


SORARE_URL = "https://api.sorare.com/graphql"

OPERATION_ID = "React/a288341ac39d1684e9492982e6dbcf7369b005b3df0afff9eeceaa81430ecf5b"


def build_payload(seed_club_slug, season_start_year):
    return {
        "operationName": "FootballClubOverviewQuery",
        "variables": {
            "slug": seed_club_slug,
            "seasonStartYear": season_start_year
        },
        "extensions": {
            "operationId": OPERATION_ID
        }
    }


def fetch_domestic_league(seed_club_slug, season_start_year):
    payload = build_payload(seed_club_slug, season_start_year)

    response = requests.post(
        SORARE_URL,
        json=payload,
        headers={"content-type": "application/json"},
        timeout=30
    )

    print("STATUS:", response.status_code)
    response.raise_for_status()

    data = response.json()

    if "errors" in data:
        raise Exception(data["errors"])

    club = data["data"]["football"]["club"]

    if not club:
        raise Exception(f"Club non trovato: {seed_club_slug}")

    domestic_league = club.get("domesticLeague")

    if not domestic_league:
        raise Exception(f"Nessuna domesticLeague trovata per: {seed_club_slug}")

    return domestic_league


def extract_clubs(domestic_league):
    clubs_by_slug = {}

    for stage in domestic_league.get("stages", []):
        for group in stage.get("groups", []):
            for contestant in group.get("contestants", []):
                team = contestant.get("team")

                if not team:
                    continue

                slug = team.get("slug")
                name = team.get("name")

                if slug and name:
                    clubs_by_slug[slug] = {
                        "name": name,
                        "slug": slug
                    }

    clubs = sorted(
        clubs_by_slug.values(),
        key=lambda x: x["name"]
    )

    return clubs


def save_club_list(league_key, league_name, seed_club_slug, season_start_year, domestic_league, clubs):
    output_dir = f"data/{league_key}/{season_start_year}"
    os.makedirs(output_dir, exist_ok=True)

    output_file = f"{output_dir}/club_list.json"

    output = {
        "updated_at": datetime.utcnow().isoformat(),
        "league": league_name,
        "league_key": league_key,
        "league_slug": domestic_league.get("slug"),
        "seasonStartYear": season_start_year,
        "seed_club": seed_club_slug,
        "total_clubs": len(clubs),
        "clubs": clubs
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return output_file


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
    seed_club_slug = league_config["seed_club_slug"]

    domestic_league = fetch_domestic_league(
        seed_club_slug=seed_club_slug,
        season_start_year=season_start_year
    )

    clubs = extract_clubs(domestic_league)

    if not clubs:
    raise Exception("Nessun club trovato. Controlla seed club o season.")
    
    output_file = save_club_list(
        league_key=league_key,
        league_name=league_name,
        seed_club_slug=seed_club_slug,
        season_start_year=season_start_year,
        domestic_league=domestic_league,
        clubs=clubs
    )

    print("==============================")
    print("DONE")
    print("League:", league_name)
    print("Season:", season_start_year)
    print("Seed club:", seed_club_slug)
    print("Clubs saved:", len(clubs))
    print("File created:", output_file)
    print("==============================")

    for club in clubs:
        print(f"- {club['name']} | {club['slug']}")


if __name__ == "__main__":
    main()
