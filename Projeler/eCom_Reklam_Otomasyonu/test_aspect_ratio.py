"""Quick test: Kie AI aspect_ratio validation."""
import os
import sys
import json
import requests

API_KEY = "0bf01128b0840e22108b95e484b09f76"
BASE_URL = "https://api.kie.ai/api/v1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

def test_create_task(aspect_ratio: str, label: str = ""):
    """Test a single aspect_ratio value."""
    payload = {
        "model": "bytedance/seedance-2",
        "input": {
            "prompt": "A simple red ball rolling on a table.",
            "duration": 5,
            "aspect_ratio": aspect_ratio,
            "generate_audio": False,
            "web_search": False,
        },
    }
    print(f"\n{'='*50}")
    print(f"Testing: '{aspect_ratio}' {label}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    try:
        resp = requests.post(
            f"{BASE_URL}/jobs/createTask",
            headers=HEADERS,
            json=payload,
            timeout=30,
        )
        print(f"HTTP Status: {resp.status_code}")
        data = resp.json()
        print(f"Response code: {data.get('code')}")
        print(f"Response msg: {data.get('msg')}")
        if data.get("code") == 200:
            task_id = data.get("data", {}).get("taskId", "?")
            print(f"✅ SUCCESS — taskId: {task_id}")
        else:
            print(f"❌ FAILED — code={data.get('code')}, msg={data.get('msg')}")
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")

if __name__ == "__main__":
    # Test all valid ratios
    for ratio in ["9:16", "16:9", "1:1", "4:3", "3:4", "21:9"]:
        test_create_task(ratio, "(expected valid)")
    
    # Test some invalid ratios to confirm behavior
    test_create_task("9/16", "(invalid separator)")
    test_create_task("vertical", "(invalid label)")
