import os, json, urllib.request

env_values = {}
with open("_knowledge/credentials/master.env") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"): continue
        if "=" in line:
            k, v = line.split("=", 1)
            env_values[k.strip()] = v.strip().strip('"').strip("'")

railway_token = env_values.get("RAILWAY_TOKEN")

# Notion DB check explicitly - default is the standard one but I should check if there is a specific YOUTUBE one
db_id = env_values.get("NOTION_DATABASE_ID_YOUTUBE_KAPAK")
if not db_id:
    db_id = env_values.get("NOTION_DATABASE_ID")

variables = {
    "KIE_API_KEY": env_values.get("KIE_API_KEY", ""),
    "IMGBB_API_KEY": env_values.get("IMGBB_API_KEY", ""),
    "GEMINI_API_KEY": env_values.get("GEMINI_API_KEY", ""),
    "NOTION_TOKEN": env_values.get("NOTION_TOKEN", ""),
    "NOTION_DATABASE_ID": db_id
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
# Note: Root directory should be set via builderUpdate or similar if serviceInstanceUpdate doesn't support it.
# If this fails, we can handle it in the dashboard, but let's try rootDirectory first on the service instance.
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
    print("Warning: rootDirectory/watchPaths update failed via serviceInstanceUpdate. Might need to be set manually or via builderUpdate.")

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
    print("Warning: cronSchedule failed, might be normal service.")

print("7. Triggers Deploy...")
res5 = graphql_query(f"""mutation {{ serviceInstanceRedeploy(environmentId: "{env_id}", serviceId: "{service_id}") }}""")

print("DONE.")
