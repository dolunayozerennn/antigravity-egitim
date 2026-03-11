import requests
import time
key = "97d226c568fea77abdeaedde37a6c6aa"
url = "https://api.kie.ai/api/v1/jobs/createTask"
h = {"Authorization": f"Bearer {key}"}

def run_task(payload):
    r = requests.post(url, headers=h, json={"model": "nano-banana-pro", "input": payload})
    tid = r.json()["data"]["taskId"]
    while True:
        time.sleep(5)
        r2 = requests.get(f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={tid}", headers=h)
        if r2.json()["data"]["state"] == "success":
            return r2.json()["data"]["resultJson"]
        elif r2.json()["data"]["state"] in ["failed", "error"]:
            return r2.json()["data"]["failMsg"]

print("1. image_url string:", run_task({"prompt": "A highly detailed perfume bottle", "image_url": "https://iili.io/q3BLjON.jpg"}))
print("2. image_urls array:", run_task({"prompt": "A highly detailed perfume bottle", "image_urls": ["https://iili.io/q3BLjON.jpg"]}))
print("3. just prompt:", run_task({"prompt": "A highly detailed perfume bottle"}))
