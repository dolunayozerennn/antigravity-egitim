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

q_deployments = """
query {
  deployments(input: {projectId: "8797307d-7b80-41cb-add0-976c09eaeed4", environmentId: "b8353ac5-0ec4-4785-8d72-7aae17f18e56", serviceId: "98a3be1e-f6f4-4ca2-8780-2b88bbd2125a"}) {
    edges {
      node {
        id
        status
      }
    }
  }
}
"""
res = requests.post("https://backboard.railway.app/graphql/v2", headers=headers, json={"query": q_deployments}).json()
deps = res.get("data", {}).get("deployments", {}).get("edges", [])

latest = None
for d in deps:
    if d["node"]["status"] in ["SUCCESS", "STARTING", "INITIALIZING"]:
        latest = d["node"]["id"]
        break

if latest:
    q_logs = """
    query deploymentLogs($id: String!) {
      deploymentLogs(deploymentId: $id, limit: 5000) { message }
    }
    """
    l_res = requests.post("https://backboard.railway.app/graphql/v2", headers=headers, json={"query": q_logs, "variables": {"id": latest}}).json()
    logs = [x["message"] for x in l_res.get("data", {}).get("deploymentLogs", [])]
    with open("recent_logs.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(logs[-1000:]))
    print("Logs saved to recent_logs.txt. Count:", len(logs))
