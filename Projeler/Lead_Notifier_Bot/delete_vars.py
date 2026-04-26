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
PROJECT_ID = "7c5d3081-1487-4b02-a60f-1cb7a04bb135"
ENV_ID = "a0ffd17c-0de3-4759-ba48-c04b96bb96b8"
SERVICE_ID = "2563df9f-37ac-4ab2-80f6-06ac8d19aec3"

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
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

query = """
mutation variableCollectionDelete($projectId: String!, $environmentId: String!, $serviceId: String!, $names: [String!]!) {
  variableCollectionDelete(projectId: $projectId, environmentId: $environmentId, serviceId: $serviceId, names: $names)
}
"""

res = graphql(query, {
    "projectId": PROJECT_ID,
    "environmentId": ENV_ID,
    "serviceId": SERVICE_ID,
    "names": ["NIXPACKS_BUILD_CMD", "NIXPACKS_START_CMD", "NIXPACKS_PROVIDERS", "RAILWAY_BUILD_WORKDIR"]
})
print(res)
