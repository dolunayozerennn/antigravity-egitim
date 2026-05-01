import os, json, urllib.request

env_values = {}
with open("/Users/dolunayozeren/Desktop/Antigravity/Projeler/Dolunay_YouTube_Kapak/.env") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"): continue
        if "=" in line:
            k, v = line.split("=", 1)
            env_values[k.strip()] = v.strip().strip('"').strip("'")

# also get railway token
with open("/Users/dolunayozeren/Desktop/Antigravity/_knowledge/credentials/master.env") as f:
    for line in f:
        line = line.strip()
        if line.startswith("RAILWAY_TOKEN="):
            railway_token = line.split("=", 1)[1].strip().strip('"').strip("'")
            break

variables = {
    "KIE_API_KEY": env_values.get("KIE_API_KEY", ""),
    "IMGBB_API_KEY": env_values.get("IMGBB_API_KEY", ""),
    "GEMINI_API_KEY": env_values.get("GEMINI_API_KEY", ""),
    "NOTION_TOKEN": env_values.get("NOTION_TOKEN", ""),
    "NOTION_DATABASE_ID": env_values.get("NOTION_DATABASE_ID", ""),
    "SCREENSHOT_API_KEY": "128GKV1-WP4MPY5-PSMHEFD-5HTARAE",
    "PYTHONUNBUFFERED": "1"
}

def graphql_query(query, vars_payload=None):
    req = urllib.request.Request("https://backboard.railway.app/graphql/v2", method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {railway_token}")
    data = {"query": query}
    if vars_payload:
        data["variables"] = vars_payload
    req.data = json.dumps(data).encode("utf-8")
    resp = urllib.request.urlopen(req)
    out = json.loads(resp.read().decode("utf-8"))
    if "errors" in out:
        print("GRAPHQL ERROR:", json.dumps(out["errors"], indent=2))
        import sys; sys.exit(1)
    return out

print("1. Creating Project...")
res1 = graphql_query("""mutation { projectCreate(input: { name: "dolunay-youtube-kapak" }) { id environments { edges { node { id name } } } } }""")
project_id = res1["data"]["projectCreate"]["id"]
env_id = res1["data"]["projectCreate"]["environments"]["edges"][0]["node"]["id"]
print("Project ID:", project_id)
print("Env ID:", env_id)

print("2. Creating Service from Mono-repo...")
res2 = graphql_query(f"""mutation {{ serviceCreate(input: {{ projectId: "{project_id}", name: "youtube-kapak-worker", source: {{ repo: "dolunayozerennn/antigravity-egitim" }}, branch: "main" }}) {{ id name }} }}""")
service_id = res2["data"]["serviceCreate"]["id"]
print("Service ID:", service_id)

vars_str = "\\n".join([f'{k}: "{v}"' for k, v in variables.items() if v])
print("3. Updating Environment Variables...")
res3 = graphql_query(f"""mutation {{ variableCollectionUpsert(input: {{ projectId: "{project_id}", environmentId: "{env_id}", serviceId: "{service_id}", variables: {{ {vars_str} }} }}) }}""")

print("4. Updating Service Settings (Cron, Start Cmd)...")
res4 = graphql_query(f"""mutation {{
  serviceInstanceUpdate(
    serviceId: "{service_id}",
    environmentId: "{env_id}",
    input: {{
      startCommand: "python main.py",
      restartPolicyType: ON_FAILURE,
      restartPolicyMaxRetries: 3
    }}
  )
}}""")

print("5. Updating Builder Settings (Root Directory)...")
try:
    res4_builder = graphql_query(f"""mutation {{
      serviceInstanceUpdate(
        serviceId: "{service_id}",
        environmentId: "{env_id}",
        input: {{
          rootDirectory: "Projeler/Dolunay_YouTube_Kapak",
          watchPaths: ["Projeler/Dolunay_YouTube_Kapak/**"]
        }}
      )
    }}""")
except SystemExit:
    print("Warning: rootDirectory update failed via serviceInstanceUpdate.")

print("6. Updating Cron Schedule...")
try:
    res4_cron = graphql_query(f"""mutation {{
      serviceInstanceUpdate(
        serviceId: "{service_id}",
        environmentId: "{env_id}",
        input: {{
          cronSchedule: "0 10 * * *"
        }}
      )
    }}""")
except SystemExit:
    print("Warning: cronSchedule failed")

print("7. Triggers Deploy...")
res5 = graphql_query(f"""mutation {{ serviceInstanceRedeploy(environmentId: "{env_id}", serviceId: "{service_id}") }}""")

print("DONE. Project:", project_id, "Service:", service_id, "Env:", env_id)
