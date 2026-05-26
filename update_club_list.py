import os
import json
import argparse
import requests
from datetime import datetime
from config import LEAGUES


API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def fetch_clubs(api_league_id, season):
    url = f"{BASE_URL}/teams"

    headers = {
        "x-apisports-key": API_KEY
    }

    params = {
        "league": api_league_id,
        "season": season
    }

    response = requests.get(url, headers=headers, params=params)

    print(f"STATUS: {response.status_code}")

    if response.status_code != 200:
        raise Exception(f"API error: {response.text}")

    data = response.json()

    clubs = []

    for item in data.get("response", []):
        team = item.get("team", {})
        venue = item.get("venue", {})

        clubs.append({
            "api_team_id": team.get("id"),
            "name": team.get("name"),
            "code": team.get("code"),
            "country": team.get("country"),
            "founded": team.get("founded"),
            "national": team.get("national"),
            "logo": team.get("logo"),
            "venue_name": venue.get("name"),
            "venue_city": venue.get("city")
        })

    return clubs


def save_club_list(league_slug, season, league_info, clubs):
    folder = f"data/{league_slug}/{season}"
    ensure_dir(folder)

    output_path = f"{folder}/club_list.json"

    payload = {
        "league_slug": league_slug,
        "league_name": league_info["name"],
        "api_league_id": league_info["api_league_id"],
        "country": league_info["country"],
        "season": season,
        "created_at": datetime.utcnow().isoformat(),
        "clubs_count": len(clubs),
        "clubs": clubs
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return output_path


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--league",
        required=True,
        choices=LEAGUES.keys(),
        help="Liga da aggiornare: belgium, croatia, segunda, bundesliga2"
    )

    parser.add_argument(
        "--season",
        required=True,
        type=int,
        help="Stagione API, esempio 2026"
    )

    args = parser.parse_args()

    if not API_KEY:
        raise Exception("Manca API_FOOTBALL_KEY nelle variabili ambiente.")

    league_slug = args.league
    season = args.season
    league_info = LEAGUES[league_slug]

    clubs = fetch_clubs(
        api_league_id=league_info["api_league_id"],
        season=season
    )

    output_path = save_club_list(
        league_slug=league_slug,
        season=season,
        league_info=league_info,
        clubs=clubs
    )

    print("==============================")
    print("DONE")
    print(f"League: {league_info['name']}")
    print(f"Season: {season}")
    print(f"Clubs saved: {len(clubs)}")
    print(f"File created: {output_path}")


if __name__ == "__main__":
    main()
