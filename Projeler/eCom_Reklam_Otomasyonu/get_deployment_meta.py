import requests
import json
token = "14ac7442-43fc-480a-b7e2-e8b5dacf1bb3"
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
