#!/bin/bash
export KIE_API_KEY=$(grep '^KIE_API_KEY=' /Users/dolunayozeren/Desktop/Antigravity/Projeler/Dolunay_YouTube_Kapak/.env | cut -d= -f2 | tr -d '"' | tr -d '\r')
export IMGBB_API_KEY=$(grep '^IMGBB_API_KEY=' /Users/dolunayozeren/Desktop/Antigravity/Projeler/Dolunay_YouTube_Kapak/.env | cut -d= -f2 | tr -d '"' | tr -d '\r')
export GEMINI_API_KEY=$(grep '^GEMINI_API_KEY=' /Users/dolunayozeren/Desktop/Antigravity/Projeler/Dolunay_YouTube_Kapak/.env | cut -d= -f2 | tr -d '"' | tr -d '\r')
export NOTION_TOKEN=$(grep '^NOTION_TOKEN=' /Users/dolunayozeren/Desktop/Antigravity/Projeler/Dolunay_YouTube_Kapak/.env | cut -d= -f2 | tr -d '"' | tr -d '\r')
export NOTION_DATABASE_ID=$(grep '^NOTION_DATABASE_ID=' /Users/dolunayozeren/Desktop/Antigravity/Projeler/Dolunay_YouTube_Kapak/.env | cut -d= -f2 | tr -d '"' | tr -d '\r')
export RAILWAY_TOKEN=$(grep '^RAILWAY_TOKEN=' /Users/dolunayozeren/Desktop/Antigravity/_knowledge/credentials/master.env | cut -d= -f2 | tr -d '"' | tr -d '\r')

echo "Creating Project..."
RES1=$(curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -d '{"query": "mutation { projectCreate(input: { name: \"dolunay-youtube-kapak\" }) { id environments { edges { node { id name } } } } }"}')

PROJECT_ID=$(echo $RES1 | grep -o 'projectCreate":{"id":"[^"]*' | cut -d'"' -f4)
ENV_ID=$(echo $RES1 | grep -o 'environments":{"edges":\[{"node":{"id":"[^"]*' | cut -d'"' -f5)
echo "Project: $PROJECT_ID, Env: $ENV_ID"

echo "Creating Service..."
RES2=$(curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -d "{\"query\": \"mutation { serviceCreate(input: { projectId: \\\"$PROJECT_ID\\\", name: \\\"youtube-kapak-worker\\\", source: { repo: \\\"dolunayozerennn/antigravity-egitim\\\" }, branch: \\\"main\\\" }) { id name } }\"}")

SERVICE_ID=$(echo $RES2 | grep -o 'serviceCreate":{"id":"[^"]*' | cut -d'"' -f4)
echo "Service: $SERVICE_ID"

echo "Updating Environment Variables..."
VARS="KIE_API_KEY: \\\"$KIE_API_KEY\\\", IMGBB_API_KEY: \\\"$IMGBB_API_KEY\\\", GEMINI_API_KEY: \\\"$GEMINI_API_KEY\\\", NOTION_TOKEN: \\\"$NOTION_TOKEN\\\", NOTION_DATABASE_ID: \\\"$NOTION_DATABASE_ID\\\", SCREENSHOT_API_KEY: \\\"128GKV1-WP4MPY5-PSMHEFD-5HTARAE\\\", PYTHONUNBUFFERED: \\\"1\\\""
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -d "{\"query\": \"mutation { variableCollectionUpsert(input: { projectId: \\\"$PROJECT_ID\\\", environmentId: \\\"$ENV_ID\\\", serviceId: \\\"$SERVICE_ID\\\", variables: { $VARS } }) }\"}" | grep -o 'variableCollectionUpsert":true'

echo "Updating Service Settings (Start Cmd, Cron, RootDir)..."
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -d "{\"query\": \"mutation { serviceInstanceUpdate(serviceId: \\\"$SERVICE_ID\\\", environmentId: \\\"$ENV_ID\\\", input: { startCommand: \\\"python main.py\\\", rootDirectory: \\\"Projeler/Dolunay_YouTube_Kapak\\\", watchPaths: [\\\"Projeler/Dolunay_YouTube_Kapak/**\\\"], restartPolicyType: ON_FAILURE, restartPolicyMaxRetries: 3, cronSchedule: \\\"0 10 * * *\\\" }) }\"}" | grep -o 'serviceInstanceUpdate":true'

echo "Triggering Deploy..."
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -d "{\"query\": \"mutation { serviceInstanceRedeploy(environmentId: \\\"$ENV_ID\\\", serviceId: \\\"$SERVICE_ID\\\") }\"}" | grep -o 'serviceInstanceRedeploy":true'

echo "Completed. Settings applied."
