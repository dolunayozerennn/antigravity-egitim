import urllib.request
import json
import sys

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

# token variable
token_val = get_railway_token()
TOKEN = token_val
service_id = "2563df9f-37ac-4ab2-80f6-06ac8d19aec3"

def graphql(query, variables=None):
    req = urllib.request.Request(
        "https://backboard.railway.app/graphql/v2",
        method="POST",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        },
        data=json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        sys.exit(1)

service_query = """
query ($id: String!) {
  service(id: $id) {
    id
    name
    source {
      repo
      ... on GitHubRepository {
         repo
      }
    }
  }
}
"""

res = graphql(service_query, {"id": service_id})
print(json.dumps(res, indent=2))
