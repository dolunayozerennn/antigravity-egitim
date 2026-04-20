import requests
import json
import os

env_path = "/Users/dolunayozeren/Desktop/Antigravity/_knowledge/credentials/master.env"
api_key = None
with open(env_path) as f:
    for line in f:
        if line.startswith("ELEVENLABS_API_KEY="):
            api_key = line.strip().split("=", 1)[1].strip('"\'')
            break

if not api_key:
    print("API Key not found in master.env!")
    exit(1)

# Railway IDs
projectId = "8797307d-7b80-41cb-add0-976c09eaeed4"
environmentId = "b8353ac5-0ec4-4785-8d72-7aae17f18e56"
serviceId = "98a3be1e-f6f4-4ca2-8780-2b88bbd2125a"

railway_token = "14ac7442-43fc-480a-b7e2-e8b5dacf1bb3"
headers = {"Authorization": f"Bearer {railway_token}", "Content-Type": "application/json"}

# Upsert variable mutation
mutation = """
mutation variableUpsert($input: VariableUpsertInput!) {
    variableUpsert(input: $input)
}
"""

variables = {
    "input": {
        "projectId": projectId,
        "environmentId": environmentId,
        "serviceId": serviceId,
        "name": "ELEVENLABS_API_KEY",
        "value": api_key,
        "skipDeploys": False
    }
}

res = requests.post(
    "https://backboard.railway.app/graphql/v2",
    headers=headers,
    json={"query": mutation, "variables": variables}
)

if res.status_code == 200:
    data = res.json()
    if "errors" in data:
        print("GraphQL Error:", json.dumps(data["errors"], indent=2))
    else:
        print("Success! Variable upserted. Railway should trigger a new deployment now.")
        print(json.dumps(data, indent=2))
else:
    print("HTTP Error", res.status_code)
    print(res.text)
