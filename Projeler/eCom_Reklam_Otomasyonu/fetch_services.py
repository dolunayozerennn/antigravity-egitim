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

# Get all services in project
q_project = """
query {
  project(id: "8797307d-7b80-41cb-add0-976c09eaeed4") {
    name
    services {
      edges {
        node {
          id
          name
        }
      }
    }
  }
}
"""
print("Fetching services...")
res = requests.post("https://backboard.railway.app/graphql/v2", headers=headers, json={"query": q_project}).json()
try:
    services = res["data"]["project"]["services"]["edges"]
except KeyError:
    print(json.dumps(res, indent=2))
    exit()

for s in services:
    s_id = s["node"]["id"]
    s_name = s["node"]["name"]
    print(f"Service: {s_name} ({s_id})")
    
    # Get deployments for service
    q_deps = """
    query($projectId: String!, $serviceId: String!) {
      deployments(input: {projectId: $projectId, serviceId: $serviceId}) {
        edges {
          node {
            id
            status
            environmentId
            createdAt
          }
        }
      }
    }
    """
    deps_res = requests.post("https://backboard.railway.app/graphql/v2", headers=headers, json={
        "query": q_deps,
        "variables": {
            "projectId": "8797307d-7b80-41cb-add0-976c09eaeed4",
            "serviceId": s_id
        }
    }).json()
    deps = deps_res.get("data", {}).get("deployments", {}).get("edges", [])
    
    # Only print SUCCESS or STARTING
    active = [d["node"] for d in deps if d["node"]["status"] in ["SUCCESS", "STARTING", "INITIALIZING"]]
    for d in active[:3]:
        print(f"  -> Dep: {d['id']}, Status: {d['status']}, Env: {d['environmentId']}, Created: {d['createdAt']}")
