import urllib.request
import json

query = """
{
  __type(name: "ServiceSourceInput") {
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
import os

def get_railway_token():
    try:
        with open("/Users/dolunayozeren/Desktop/Antigravity/_knowledge/credentials/master.env", "r") as f:
            for line in f:
                if line.startswith("RAILWAY_TOKEN="):
                    return line.strip().split("=")[1].strip('\'"')
    except:
        pass
    return os.environ.get("RAILWAY_TOKEN", "")

req.add_header("Content-Type", "application/json")
req.add_header("Authorization", f"Bearer {get_railway_token()}")

try:
    with urllib.request.urlopen(req) as response:
        print(response.read().decode())
except Exception as e:
    print(e)
