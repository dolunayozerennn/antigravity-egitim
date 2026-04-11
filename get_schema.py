import urllib.request
import json

query = """
{
  __type(name: "ServiceUpdateInput") {
    inputFields {
      name
      type { name kind }
    }
  }
}
"""

req = urllib.request.Request(
    "https://backboard.railway.app/graphql/v2",
    data=json.dumps({"query": query}).encode()
)
req.add_header("Content-Type", "application/json")
req.add_header("Authorization", "Bearer 14ac7442-43fc-480a-b7e2-e8b5dacf1bb3")

try:
    with urllib.request.urlopen(req) as response:
        print(response.read().decode())
except Exception as e:
    print(e)
