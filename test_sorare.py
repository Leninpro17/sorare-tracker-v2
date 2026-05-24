import requests

query = """
{
  football {
    clubs(first: 1) {
      name
      slug
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
