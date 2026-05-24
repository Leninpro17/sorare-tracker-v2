import requests
import json

URL = "https://api.sorare.com/graphql"

query = """
query FootballClubOverviewQuery($slug: String!, $seasonStartYear: Int!) {
  football {
    club(slug: $slug) {
      name
      slug
      code

      country {
        name
        slug
      }

      activeCompetitions {
        displayName
        slug
      }

      domesticLeague {
        displayName
        slug

        stages {
          groups {
            contestants {
              rank
              points
              matchesPlayed
              matchesWon
              matchesDrawn
              matchesLost
              goalsFor
              goalsAgainst

              team {
                name
                slug
              }
            }
          }
        }
      }
    }
  }
}
"""

payload = {
    "operationName": "FootballClubOverviewQuery",
    "variables": {
        "slug": "genk-genk",
        "seasonStartYear": 2025
    },
    "query": query
}

headers = {
    "Content-Type": "application/json"
}

r = requests.post(
    URL,
    headers=headers,
    json=payload,
    timeout=30
)

print(r.status_code)

data = r.json()

with open("genk.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("saved genk.json")
