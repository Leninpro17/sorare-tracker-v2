import requests

query = """
{
  __type(name: "Club") {
    name
    fields {
      name
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
