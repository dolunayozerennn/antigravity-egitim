import requests

token = "14ac7442-43fc-480a-b7e2-e8b5dacf1bb3"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Query to find mutations matching "trigger" or "deploy" or "update"
q = """
{
  __schema {
    mutationType {
      fields {
        name
        args {
          name
        }
      }
    }
  }
}
"""
res = requests.post("https://backboard.railway.app/graphql/v2", headers=headers, json={"query": q}).json()
fields = res.get("data", {}).get("__schema", {}).get("mutationType", {}).get("fields", [])
mutations = []
for f in fields:
    name = f["name"]
    if "deploy" in name.lower() or "trigger" in name.lower() or "service" in name.lower():
        mutations.append({
            "name": name,
            "args": [arg["name"] for arg in f["args"]]
        })

for m in mutations:
    print(f"{m['name']}: {', '.join(m['args'])}")
