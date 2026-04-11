import urllib.request
import json
import time

RAILWAY_TOKEN = "14ac7442-43fc-480a-b7e2-e8b5dacf1bb3"

services = [
    {
        "name": "linkedin-text-cron",
        "serviceId": "c1b095f4-700b-4302-ac30-efe537d5935c",
        "environmentId": "2a4e2f58-b0db-4a90-9ab1-689f1f403363"
    },
    {
        "name": "linkedin-video-cron",
        "serviceId": "8e486d77-c5b1-4f70-9f29-55c8b59398f9",
        "environmentId": "d4f9b81a-8e72-432b-b64c-089ead41f636"
    },
    {
        "name": "twitter-video-cron",
        "serviceId": "55f76475-5b45-4050-93f7-723110ab470e",
        "environmentId": "1e5cfad2-c76d-4ca1-a1a5-c839a2cfdb1d"
    }
]

status_query = """
query getDeployments($environmentId: String!, $serviceId: String!) {
  deployments(input: {environmentId: $environmentId, serviceId: $serviceId}, first: 1) {
    edges {
      node {
        id
        status
      }
    }
  }
}
"""

logs_query = """
query getLogs($deploymentId: String!) {
  deploymentLogs(deploymentId: $deploymentId, limit: 100) {
    message
  }
}
"""

def graphql_request(query, variables):
    req = urllib.request.Request(
        "https://backboard.railway.app/graphql/v2",
        data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {RAILWAY_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "curl/8.6.0"
        },
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_latest_deployment(env_id, src_id):
    data = graphql_request(status_query, {"environmentId": env_id, "serviceId": src_id})
    edges = data.get("data", {}).get("deployments", {}).get("edges", [])
    if edges:
        return edges[0]["node"]
    return None

def check_logs(deployment_id, name):
    data = graphql_request(logs_query, {"deploymentId": deployment_id})
    logs = data.get("data", {}).get("deploymentLogs", [])
    text_logs = [log.get("message", "") for log in logs]
    combined = "\n".join(text_logs).lower()
    
    fatal = [kw for kw in ["attributeerror", "importerror", "syntaxerror", "traceback"] if kw in combined]
    if fatal:
        print(f"❌ FATAL ERROR IN {name}: {fatal}")
        for log in text_logs[-20:]:
            print("   " + log)
        return False
    print(f"✅ Smoke Test Passed for {name} (No Fatal Errors Found in Deploy Logs)")
    return True

completed = set()
start_time = time.time()

print("Tracking deployments (Waiting for Build SUCCESS)...")
# We will wait up to 4 minutes
while len(completed) < len(services) and time.time() - start_time < 240:
    for srv in services:
        if srv["name"] in completed: continue
        
        dep = get_latest_deployment(srv["environmentId"], srv["serviceId"])
        if not dep: continue
        
        status = dep.get("status")
        if status in ["SUCCESS", "FAILED"]:
            print(f"[{srv['name']}] Build/Deploy Status: {status}")
            check_logs(dep["id"], srv["name"])
            completed.add(srv["name"])
    
    if len(completed) < len(services):
        time.sleep(15)

if len(completed) < len(services):
    print("Timeout waiting for deployments to complete.")
