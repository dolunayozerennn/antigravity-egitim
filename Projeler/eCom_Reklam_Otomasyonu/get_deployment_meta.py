import requests
import json
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
token = token_val
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
q = """
query {
  deployments(input: {serviceId: "98a3be1e-f6f4-4ca2-8780-2b88bbd2125a"}) {
    edges {
      node {
        id
        status
        createdAt
        meta
      }
    }
  }
}
"""
res = requests.post("https://backboard.railway.app/graphql/v2", headers=headers, json={"query": q}).json()
deps = res.get("data", {}).get("deployments", {}).get("edges", [])
for d in deps:
    node = d["node"]
    if True:
        print(f"Deployment: {node['id']} at {node['createdAt']} - Status: {node['status']} - Meta: {node.get('meta')}")
