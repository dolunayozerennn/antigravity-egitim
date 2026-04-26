import requests
import sys

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

svc_id = "98a3be1e-f6f4-4ca2-8780-2b88bbd2125a"
env_id = "b8353ac5-0ec4-4785-8d72-7aae17f18e56"
commit_sha = sys.argv[1]

q = """
mutation deployCommit($commitSha: String!, $environmentId: String!, $serviceId: String!) {
  serviceInstanceDeployV2(commitSha: $commitSha, environmentId: $environmentId, serviceId: $serviceId)
}
"""
variables = {
    "commitSha": commit_sha,
    "environmentId": env_id,
    "serviceId": svc_id
}

res = requests.post(
    "https://backboard.railway.app/graphql/v2", 
    headers=headers, 
    json={"query": q, "variables": variables}
).json()

print(res)
