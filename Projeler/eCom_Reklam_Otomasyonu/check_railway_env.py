import os
import requests
import json

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
token = token_val # From master.env RAILWAY_TOKEN
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# the project id is 8797307d-7b80-41cb-add0-976c09eaeed4
# the env id is b8353ac5-0ec4-4785-8d72-7aae17f18e56
query = """
query {
    variables(projectId: "8797307d-7b80-41cb-add0-976c09eaeed4", environmentId: "b8353ac5-0ec4-4785-8d72-7aae17f18e56", serviceId: "98a3be1e-f6f4-4ca2-8780-2b88bbd2125a") {
        edges {
            node {
                name
                value
            }
        }
    }
}
"""

res = requests.post("https://backboard.railway.app/graphql/v2", headers=headers, json={"query": query})
edges = res.json().get('data', {}).get('variables', {}).get('edges', [])
print("Railway Variables:")
for edge in edges:
    name = edge['node']['name']
    val = edge['node']['value']
    if "ELEVEN" in name or "TOKEN" in name or "KEY" in name:
        print(f"{name}: {val[:5]}...{val[-5:]}")
