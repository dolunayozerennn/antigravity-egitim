from apify_client import ApifyClient

client = ApifyClient("apify_api_mGCYOhkgDAGnK4RDPP6DOUBFGoG3P225JeTn")

try:
    run = client.actor("compass/crawler-google-places").call(run_input={"searchStringsArray": ["fast food in New York"], "maxCrawledPlacesPerSearch": 2})
    print([item for item in client.dataset(run["defaultDatasetId"]).iterate_items()])
except Exception as e:
    print("Error crawler-google-places:", e)

try:
    run = client.actor("apify/google-maps-scraper").call(run_input={"searchStringsArray": ["fast food in New York"], "maxCrawledPlacesPerSearch": 2})
    print([item for item in client.dataset(run["defaultDatasetId"]).iterate_items()])
except Exception as e:
    print("Error google-maps-scraper:", e)
