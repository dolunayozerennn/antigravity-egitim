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
token = token_val
project_id = "87e24335-52c9-460f-8b2e-0f481f5501bd"
service_id = "d17abb9e-3ef1-4f50-98c1-f4290bb2f090"

query = """
query {
  deployments(input: {projectId: "%s", serviceId: "%s"}) {
    edges {
      node {
        id
        status
        createdAt
      }
    }
  }
}
""" % (project_id, service_id)

url = "https://backboard.railway.app/graphql/v2"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
data = json.dumps({"query": query}).encode()

req = urllib.request.Request(url, data=data, headers=headers)
with urllib.request.urlopen(req) as response:
    res = json.loads(response.read().decode())
    
deployments = res.get("data", {}).get("deployments", {}).get("edges", [])
if deployments:
    active_deployments = [d for d in deployments if d["node"]["status"] == "SUCCESS"]
    latest_deployment = active_deployments[0]["node"]["id"] if active_deployments else deployments[0]["node"]["id"]
    
    query_logs = """
    query {
      deploymentLogs(deploymentId: "%s", limit: 300) {
        timestamp
        message
      }
    }
    """ % latest_deployment
    
    req_logs = urllib.request.Request(url, data=json.dumps({"query": query_logs}).encode(), headers=headers)
    with urllib.request.urlopen(req_logs) as resp_logs:
        logs_data = json.loads(resp_logs.read().decode())
        logs = logs_data.get("data", {}).get("deploymentLogs", [])
        lines = [log.get("message", "") for log in logs]
        
        print("--- RECENT LOGS ---")
        print("\n".join(lines[-30:]))
        
        print("\n--- ASTRONOT MATCHES ---")
        for l in lines:
            if "astronot" in l.lower():
                print(l.strip())
        
        # also print matches for "error", "fail", "Exception" in the last 100 lines
        import re
        print("\n--- ERRORS ---")
        for l in lines[-150:]:
            if re.search(r'(error|fail|exception|Traceback|❌)', l, re.IGNORECASE):
                print(l.strip())
