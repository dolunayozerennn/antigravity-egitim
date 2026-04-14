import requests
import sys

token = "14ac7442-43fc-480a-b7e2-e8b5dacf1bb3"
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
