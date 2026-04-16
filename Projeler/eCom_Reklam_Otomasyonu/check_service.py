import os
import requests
import json
import logging

logging.basicConfig(level=logging.INFO)

token = os.environ.get("RAILWAY_TOKEN")
if not token:
    raise ValueError("RAILWAY_TOKEN environment variable is required")
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Get service details
q_service = """
query {
  service(id: "98a3be1e-f6f4-4ca2-8780-2b88bbd2125a") {
    name
    repository
    source {
      repo
      branch
      triggerConfig {
        branch
      }
    }
  }
}
"""
res = requests.post("https://backboard.railway.app/graphql/v2", headers=headers, json={"query": q_service}).json()
try:
    print(json.dumps(res, indent=2))
except Exception as e:
    logging.error("Failed to dump JSON response:", exc_info=True)
