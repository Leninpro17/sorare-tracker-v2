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

    print(f"\nScanning {club_slug}")

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

    try:
        response = requests.post(
            "https://api.sorare.com/graphql",
            json=payload,
            headers={
                "content-type": "application/json"
            },
            timeout=30
        )

        print("STATUS:", response.status_code)

        if response.status_code != 200:
            continue

        data = response.json()

        club = data["data"]["football"]["club"]

        club_name = club["name"]

        memberships = club["activeMemberships"]["nodes"]

        print(
            f"Club: {club_name} | Players: {len(memberships)}"
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
                    if player.get("country")
                    else None
                ),
                "club": club_name,
                "club_slug": club_slug,
                "avatarPictureUrl": player.get(
                    "avatarPictureUrl"
                ),
                "membershipStartDate": membership.get(
                    "startDate"
                )
            })

    except Exception as e:
        print("ERROR:", club_slug)
        print(str(e))

output = {
    "updated_at": datetime.utcnow().isoformat(),
    "league": "Jupiler Pro League",
    "total_players": len(all_players),
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

print("\n==============================")
print("DONE")
print("Players saved:", len(all_players))
print("File created: player_data.json")
print("==============================")
