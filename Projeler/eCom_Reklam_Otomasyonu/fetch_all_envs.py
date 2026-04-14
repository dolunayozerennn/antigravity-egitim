import requests
import json

token = "14ac7442-43fc-480a-b7e2-e8b5dacf1bb3"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Get all environments in project
q_project = """
query {
  project(id: "8797307d-7b80-41cb-add0-976c09eaeed4") {
    environments {
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
print("Fetching environments...")
res = requests.post("https://backboard.railway.app/graphql/v2", headers=headers, json={"query": q_project}).json()
envs = res["data"]["project"]["environments"]["edges"]

for e in envs:
    env_id = e["node"]["id"]
    env_name = e["node"]["name"]
    print(f"\nEnvironment: {env_name} ({env_id})")
    
    # Get deployments for env
    q_deps = """
    query {
      deployments(input: {projectId: "8797307d-7b80-41cb-add0-976c09eaeed4", environmentId: "%s", serviceId: "98a3be1e-f6f4-4ca2-8780-2b88bbd2125a"}) {
        edges {
          node {
            id
            status
            createdAt
          }
        }
      }
    }
    """ % env_id
    deps_res = requests.post("https://backboard.railway.app/graphql/v2", headers=headers, json={"query": q_deps}).json()
    deps = deps_res.get("data", {}).get("deployments", {}).get("edges", [])
    
    active = [d["node"] for d in deps if d["node"]["status"] in ["SUCCESS", "STARTING", "INITIALIZING"]]
    if not active:
        print("  No active deployments.")
    for d in active:
        print(f"  -> Dep: {d['id']}, Status: {d['status']}, Created: {d['createdAt']}")
