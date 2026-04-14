import requests
import sys

token = "14ac7442-43fc-480a-b7e2-e8b5dacf1bb3"
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
