import requests
import json
import time

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
RAILWAY_TOKEN = token_val

deployments = [
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

query = """
mutation deploymentTrigger($environmentId: String!, $serviceId: String!) {
  environmentTriggersDeploy(input: {environmentId: $environmentId, serviceId: $serviceId})
}
"""

headers = {
    "Authorization": f"Bearer {RAILWAY_TOKEN}",
    "Content-Type": "application/json"
}

results = []

for dep in deployments:
    payload = {
        "query": query,
        "variables": {
            "environmentId": dep["environmentId"],
            "serviceId": dep["serviceId"]
        }
    }
    
    response = requests.post("https://backboard.railway.app/graphql/v2", headers=headers, json=payload)
    data = response.json()
    
    if "data" in data and data["data"].get("environmentTriggersDeploy"):
        print(f"✅ {dep['name']}: Deployment triggered.")
        results.append((dep['name'], True))
    else:
        print(f"❌ {dep['name']}: Deployment failed. Response: {json.dumps(data)}")
        results.append((dep['name'], False))
    time.sleep(1)

print("Check complete.")
