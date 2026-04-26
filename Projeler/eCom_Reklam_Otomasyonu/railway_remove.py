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

# The old deployment ID
dep_id = "a72b9e6f-ea74-4dc8-9457-af89b26374b2"

q = """
mutation deploymentRemove($id: String!) {
  deploymentRemove(id: $id)
}
"""
variables = {
    "id": dep_id
}

res = requests.post(
    "https://backboard.railway.app/graphql/v2", 
    headers=headers, 
    json={"query": q, "variables": variables}
).json()

print(res)
