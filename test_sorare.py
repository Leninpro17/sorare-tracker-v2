import requests

query = """
{
  football {
    clubs(first: 5) {
      nodes {
        name
      }
    }
  }
}
"""

r = requests.post(
    "https://api.sorare.com/graphql",
    json={"query": query}
)

print(r.status_code)
print(r.text)
