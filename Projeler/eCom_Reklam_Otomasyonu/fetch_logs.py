import requests
import json

token = "14ac7442-43fc-480a-b7e2-e8b5dacf1bb3"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# 1. Get latest deployment
q_deployments = """
query {
  deployments(input: {projectId: "8797307d-7b80-41cb-add0-976c09eaeed4", environmentId: "b8353ac5-0ec4-4785-8d72-7aae17f18e56", serviceId: "98a3be1e-f6f4-4ca2-8780-2b88bbd2125a"}) {
    edges {
      node {
        id
        status
        createdAt
      }
    }
  }
}
"""
res = requests.post("https://backboard.railway.app/graphql/v2", headers=headers, json={"query": q_deployments}).json()
deps = res.get("data", {}).get("deployments", {}).get("edges", [])
if not deps:
    print("No deployments found or error:", json.dumps(res))
    exit()

latest_deploy_id = None
for d in deps:
    # Get the latest SUCCESS or STARTING
    if d["node"]["status"] in ["SUCCESS", "STARTING", "INITIALIZING"]:
        latest_deploy_id = d["node"]["id"]
        break
if not latest_deploy_id:
    latest_deploy_id = deps[0]["node"]["id"]

if latest_deploy_id:
    print(f"Fetching logs for {latest_deploy_id}")
    # 2. Get logs
    q_logs = """
    query deploymentLogs($id: String!) {
      deploymentLogs(deploymentId: $id) { message }
    }
    """
    l_res = requests.post("https://backboard.railway.app/graphql/v2", headers=headers, json={"query": q_logs, "variables": {"id": latest_deploy_id}}).json()
    logs = [x["message"] for x in l_res.get("data", {}).get("deploymentLogs", [])]
    with open("latest_logs.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(logs[-1500:]))
    print(f"Saved latest logs to latest_logs.txt (Deployment: {latest_deploy_id})")
