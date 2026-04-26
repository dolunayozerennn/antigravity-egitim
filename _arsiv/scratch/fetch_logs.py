import json
import urllib.request

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

def query_railway(query, variables=None):
    req = urllib.request.Request(
        "https://backboard.railway.app/graphql/v2",
        data=json.dumps({"query": query, "variables": variables or {}}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "Antigravity/1.0",
            "Accept": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"GraphQL Error: {e}")
        return None

services = {
    "ceren-izlenme-notifier": {"project": "b5117788-3979-45b3-a92c-eae3606e0dc2", "service": "058d3d5c-9589-4c49-aca2-f6965207aa38"},
    "akilli-watchdog": {"project": "ec3ea7b1-9bdb-4886-a197-026ee2d2126c", "service": "ddb6ddd6-4918-4b27-bd5c-946bb829bc42"},
    "linkedin-text-cron": {"project": "5465753a-2653-400a-ae3a-d4593de9c40e", "service": "c1b095f4-700b-4302-ac30-efe537d5935c"},
    "twitter-video-cron": {"project": "24c3d0d1-58e7-4213-826b-c7e2d1c45a30", "service": "55f76475-5b45-4050-93f7-723110ab470e"}
}

for name, ids in services.items():
    print(f"\n--- {name} ---")
    query = """
    query {
      deployments(input: {projectId: "%s", serviceId: "%s"}) {
        edges {
          node {
            id
            createdAt
            status
          }
        }
      }
    }
    """ % (ids["project"], ids["service"])
    res = query_railway(query)
    edges = res.get("data", {}).get("deployments", {}).get("edges", [])
    if edges:
        latest = edges[0]["node"]
        print(f"Latest deploy: {latest['id']} | Status: {latest['status']} | Created: {latest['createdAt']}")
        log_query = """
        query {
          deploymentLogs(deploymentId: "%s", limit: 500) {
            message
          }
        }
        """ % latest["id"]
        log_res = query_railway(log_query)
        logs = log_res.get("data", {}).get("deploymentLogs", [])
        print("Last 15 log lines:")
        for log in logs[-15:]:
            print(log["message"].strip())
    else:
        print("No deployments found.")

