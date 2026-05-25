import json
import requests
from datetime import datetime

OUTPUT_FILE = "club_list.json"

SEED_CLUB_SLUG = "genk-genk"
SEASON_START_YEAR = 2025
LEAGUE_NAME = "Jupiler Pro League"

OPERATION_ID = "React/a288341ac39d1684e9492982e6dbcf7369b005b3df0afff9eeceaa81430ecf5b"

payload = {
    "operationName": "FootballClubOverviewQuery",
    "variables": {
        "slug": SEED_CLUB_SLUG,
        "seasonStartYear": SEASON_START_YEAR
    },
    "extensions": {
        "operationId": OPERATION_ID
    }
}

response = requests.post(
    "https://api.sorare.com/graphql",
    json=payload,
    headers={"content-type": "application/json"},
    timeout=30
)

print("STATUS:", response.status_code)
response.raise_for_status()

data = response.json()

club = data["data"]["football"]["club"]
domestic_league = club["domesticLeague"]

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

output = {
    "updated_at": datetime.utcnow().isoformat(),
    "league": LEAGUE_NAME,
    "league_slug": domestic_league.get("slug"),
    "seasonStartYear": SEASON_START_YEAR,
    "seed_club": SEED_CLUB_SLUG,
    "total_clubs": len(clubs),
    "clubs": clubs
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("==============================")
print("DONE")
print("League:", LEAGUE_NAME)
print("Season:", SEASON_START_YEAR)
print("Clubs saved:", len(clubs))
print("File created:", OUTPUT_FILE)
print("==============================")

for club in clubs:
    print(f"- {club['name']} | {club['slug']}")
