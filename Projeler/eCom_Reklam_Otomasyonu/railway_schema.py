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
token = token_val
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Get the input type fields
q = """
{
  __type(name: "VariableUpsertInput") {
    name
    inputFields {
      name
      type {
        name
        kind
        ofType {
          name
          kind
        }
      }
    }
  }
}
"""
res = requests.post("https://backboard.railway.app/graphql/v2", headers=headers, json={"query": q}).json()
print(json.dumps(res, indent=2))
