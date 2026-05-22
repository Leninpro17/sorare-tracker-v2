import json
import os
import requests
import time

API_KEY = os.environ["FOOTBALL_DATA_API_KEY"]

HEADERS = {
    "X-Auth-Token": API_KEY
}

BASE_URL = "https://api.football-data.org/v4"

# IMPORTANTE:
# Prima esecuzione: stampa tutte le competizioni
# per trovare il codice corretto della Jupiler Pro League.

def get_competitions():
    r = requests.get(
        f"{BASE_URL}/competitions",
        headers=HEADERS
    )

    r.raise_for_status()

    data = r.json()

    for comp in data["competitions"]:
        print(
            comp["id"],
            comp["code"],
            comp["name"]
        )

def build_players(competition_code):

    teams_url = (
        f"{BASE_URL}/competitions/"
        f"{competition_code}/teams"
    )

    r = requests.get(
        teams_url,
        headers=HEADERS
    )

    r.raise_for_status()

    teams = r.json()["teams"]

    players = {}

    for team in teams:

        team_id = team["id"]

        print(
            f"Downloading squad: "
            f"{team['name']}"
        )

        squad_url = (
            f"{BASE_URL}/teams/{team_id}"
        )

        squad_response = requests.get(
            squad_url,
            headers=HEADERS
        )

        squad_response.raise_for_status()

        squad_data = squad_response.json()

        for player in squad_data.get(
            "squad",
            []
        ):

            name = player["name"]

            dob = player.get(
                "dateOfBirth",
                ""
            )

            age = 25

            if dob:
                try:
                    birth_year = int(
                        dob[:4]
                    )
                    age = 2026 - birth_year
                except:
                    pass

            position = (
                player.get(
                    "position",
                    "MID"
                )
            )

            players[name] = {
                "team": team["name"],
                "age": age,
                "u23": age <= 23,
                "starter": False,
                "price": 0,
                "position": position,
                "l15": 0,
                "l40": 0,
                "league": "Jupiler Pro League",
                "owned": False
            }

        time.sleep(1)

    with open(
        "player_data.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            players,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"Saved {len(players)} players"
    )

if __name__ == "__main__":

    # Prima esecuzione:
    get_competitions()

    # Quando trovi il codice corretto:
    # build_players("XXX")
