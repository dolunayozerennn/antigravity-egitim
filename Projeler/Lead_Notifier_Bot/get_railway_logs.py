import urllib.request
import json
import sys

TOKEN = "14ac7442-43fc-480a-b7e2-e8b5dacf1bb3"
PROJECT_ID = "7c5d3081-1487-4b02-a60f-1cb7a04bb135"
ENV_ID = "a0ffd17c-0de3-4759-ba48-c04b96bb96b8"
service_id = "2563df9f-37ac-4ab2-80f6-06ac8d19aec3"

def graphql(query, variables=None):
    req = urllib.request.Request(
        "https://backboard.railway.app/graphql/v2",
        method="POST",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        },
        data=json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        sys.exit(1)

deployments_query = """
query ($projectId: String!, $environmentId: String!, $serviceId: String!) {
  deployments(
    input: {projectId: $projectId, environmentId: $environmentId, serviceId: $serviceId}
  ) {
    edges {
      node {
        id
        status
        createdAt
      }
    }
  }
}
"""

res = graphql(deployments_query, {
    "projectId": PROJECT_ID,
    "environmentId": ENV_ID,
    "serviceId": service_id
})

if 'errors' in res:
    print(res['errors'])
else:
    edges = res['data']['deployments']['edges']
    if edges:
        latest = edges[0]['node']
        print(f"Latest deployment: {latest['id']}, Status: {latest['status']}")
        
        # Get logs for latest deployment
        logs_query = """
        query ($deploymentId: String!) {
          deploymentLogs(deploymentId: $deploymentId) {
            message
          }
        }
        """
        logs_res = graphql(logs_query, {"deploymentId": latest['id']})
        if 'errors' not in logs_res:
            logs = logs_res['data']['deploymentLogs']
            print("\n--- DEPLOYMENT LOGS ---")
            for log in logs[-50:]:  # last 50 lines
                print(log['message'])
    else:
        print("No deployments found.")
