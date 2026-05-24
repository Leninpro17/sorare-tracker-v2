import requests
import json
from datetime import datetime

JUPILER_CLUBS = [
    "genk-genk",
    "club-brugge-brugge",
    "anderlecht-bruxelles-brussel",
    "union-saint-gilloise-bruxelles-brussels",
    "gent-gent",
    "antwerp-deurne",
    "sporting-charleroi-charleroi",
    "sint-truiden-sint-truiden-st-trond",
    "mechelen-mechelen-malines",
    "oh-leuven-heverlee",
    "westerlo-westerlo",
    "standard-liege-liege-luik",
    "cercle-brugge-brugge",
    "dender-denderleeuw",
    "zulte-waregem-waregem",
    "la-louviere-la-louviere"
]

all_players = []

for club_slug in JUPILER_CLUBS:

    print(f"Scanning {club_slug}")

    payload = {
        "operationName": "FootballClubOverviewQuery",
        "variables": {
            "slug": club_slug,
            "seasonStartYear": 2025
        },
        "extensions": {
            "operationId": "React/a288341ac39d1684e9492982e6dbcf7369b005b3df0afff9eeceaa81430ecf5b"
        }
    }

    r = requests.post(
        "https://api.sorare.com/graphql",
        json=payload,
        headers={"content-type": "application/json"}
    )

    if r.status_code != 200:
        print("ERROR:", club_slug, r.status_code)
        continue

    data = r.json()

    try:
        club = data["data"]["football"]["club"]

        club_name = club["name"]

        memberships = (
            club["activeMemberships"]["nodes"]
        )

        for membership in memberships:

            player = membership["player"]

            all_players.append({
                "slug": player.get("slug"),
                "displayName": player.get("displayName"),
                "position": player.get("position"),
                "country": (
                    player.get("country", {})
                    .get("name")
                ),
                "club": club_name,
                "club_slug": club_slug,
                "avatar": player.get("avatarPictureUrl")
            })

    except Exception as e:
        print("ERROR PARSING", club_slug, e)

output = {
    "updated_at": datetime.utcnow().isoformat(),
    "league": "Jupiler Pro League",
    "players": all_players
}

with open(
    "player_data.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        output,
        f,
        indent=2,
        ensure_ascii=False
    )

print()
print("Players saved:", len(all_players))
print("File: player_data.json")
