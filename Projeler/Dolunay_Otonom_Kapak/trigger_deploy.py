import requests

token = "14ac7442-43fc-480a-b7e2-e8b5dacf1bb3"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

env_id = "f23dd962-8015-45aa-ab47-94e34d8023c0"
services = [
    "3afcca6e-8f29-4ea6-bc99-b212a4269e34", # reels-kapak
    "0bfc46ea-887f-4a62-a3da-bc7fb824eb3c"  # youtube-kapak
]
commit_sha = "431c6e6c0202e3c7bfcfadc1d9a8023a10cf10db"

q = """
mutation buildSpecificCommit($environmentId: String!, $serviceId: String!, $commitSha: String!) {
  serviceInstanceDeploy(environmentId: $environmentId, serviceId: $serviceId, commitSha: $commitSha)
}
"""

for svc in services:
    res = requests.post(
        "https://backboard.railway.app/graphql/v2", 
        headers=headers, 
        json={"query": q, "variables": {"environmentId": env_id, "serviceId": svc, "commitSha": commit_sha}}
    ).json()
    print(f"Service {svc}: {res}")
