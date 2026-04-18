import os
import requests

api_key = os.environ.get("KIE_API_KEY")
url = "https://api.kie.ai/api/v1/jobs/createTask"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payloads = [
    {
        "model": "nano-banana-2",
        "input": {
            "prompt": "futuristic city",
            "aspect_ratio": "16:9",
            "resolution": "1k"
        }
    },
    {
        "model": "nano-banana-2",
        "input": {
            "prompt": "futuristic city",
            "aspect_ratio": "16:9",
            # no resolution
        }
    },
    {
        "model": "nano-banana-2",
        "input": {
            "prompt": "futuristic city",
            "aspect_ratio": "16:9",
            "resolution": "1080p"
        }
    }
]

for p in payloads:
    resp = requests.post(url, headers=headers, json=p)
    print(f"Payload with resolution {p['input'].get('resolution', 'NONE')}: {resp.status_code}")
    print(resp.text)
    print("-" * 20)

