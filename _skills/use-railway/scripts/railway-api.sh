#!/usr/bin/env bash
# Railway GraphQL API helper for Antigravity Ecosystem
# Usage: railway-api.sh '<graphql-query>' ['<variables-json>']

set -e

if ! command -v jq &>/dev/null; then
  echo '{"error": "jq not installed. Install with: brew install jq"}'
  exit 1
fi

ENV_FILE="/Users/dolunayozeren/Desktop/Antigravity/_knowledge/credentials/master.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo '{"error": "master.env not found. Please ensure _knowledge/credentials/master.env exists."}'
  exit 1
fi

# Extract the RAILWAY_TOKEN from the master.env file
TOKEN=$(grep -E '^RAILWAY_TOKEN=' "$ENV_FILE" | cut -d '=' -f 2- | tr -d '"' | tr -d "'")

if [[ -z "$TOKEN" ]]; then
  echo '{"error": "No RAILWAY_TOKEN found in master.env"}'
  exit 1
fi

if [[ -z "$1" ]]; then
  echo '{"error": "No query provided"}'
  exit 1
fi

# Build payload with query and optional variables
if [[ -n "$2" ]]; then
  PAYLOAD=$(jq -n --arg q "$1" --argjson v "$2" '{query: $q, variables: $v}')
else
  PAYLOAD=$(jq -n --arg q "$1" '{query: $q}')
fi

curl -s https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD"
