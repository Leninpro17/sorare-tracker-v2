import requests

query = """
query {
  football {
    __typename
  }
}
"""

r = requests.post(
    "https://api.sorare.com/graphql",
    json={"query": query}
)

print(r.status_code)
print(r.text[:500])
