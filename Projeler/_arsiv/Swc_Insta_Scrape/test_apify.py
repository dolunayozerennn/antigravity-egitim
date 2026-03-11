import os
from apify_client import ApifyClient

# Replace with the user's API Key
API_KEY = "apify_api_oouPGgkmSJZ0K7PrpBfLx6FwxH4hD23SlgQP"

client = ApifyClient(API_KEY)

# Test run
run_input = {
    "keyword": "walktask",
    "resultsLimit": 100,
}

print("Running crawler-bros/instagram-keyword-search-scraper for testing...")
run = client.actor("crawler-bros/instagram-keyword-search-scraper").call(run_input=run_input)

print("Actor finished, processing results.")
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print("Item:", item.keys())
    # print some details to see what we get
    print("Owner:", item.get("ownerUsername"), item.get("ownerFullName"))
    print("Caption:", item.get("caption"))
    print("Followers:", item.get("ownerFollowers"))  # check if this exists
    print("-" * 20)
