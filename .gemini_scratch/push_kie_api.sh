#!/bin/bash
# Push kie_api.py to GitHub via API using base64 encoding
# This script reads the local file and pushes via GitHub REST API

FILE_PATH="Projeler/eCom_Reklam_Otomasyonu/services/kie_api.py"
LOCAL_PATH="/Users/dolunayozeren/Desktop/Antigravity/${FILE_PATH}"
REPO="dolunayozerennn/antigravity-egitim"
BRANCH="main"

# Get current SHA from GitHub
SHA=$(curl -s -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  "https://api.github.com/repos/${REPO}/contents/${FILE_PATH}?ref=${BRANCH}" | \
  grep '"sha"' | head -1 | sed 's/.*"sha": "//;s/".*//')

echo "Current SHA: ${SHA}"

# Base64 encode the file
CONTENT=$(base64 < "${LOCAL_PATH}")

# Create the JSON payload
cat > /tmp/push_payload.json << EOFPAYLOAD
{
  "message": "fix(eCom): kie_api.py — normalize_aspect_ratio + 422 debug logging",
  "content": "${CONTENT}",
  "sha": "${SHA}",
  "branch": "${BRANCH}"
}
EOFPAYLOAD

# Push to GitHub
curl -s -X PUT \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "Content-Type: application/json" \
  "https://api.github.com/repos/${REPO}/contents/${FILE_PATH}" \
  -d @/tmp/push_payload.json | head -5

echo "Done"
