from apify_client import ApifyClient

client = ApifyClient("apify_api_mGCYOhkgDAGnK4RDPP6DOUBFGoG3P225JeTn")

try:
    queries = "site:linkedin.com/in (Founder OR Owner OR Procurement OR Purchasing) (fast food OR fine dining OR cafe OR bakery) (New York OR New Jersey OR Chicago)"
    run = client.actor("apify/google-search-scraper").call(run_input={"queries": queries, "resultsPerPage": 10, "maxPagesPerQuery": 1})
    
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    
    for row in items:
        # print first search result
        results = row.get("organicResults", [])
        for r in results:
            print(f"Title: {r.get('title')}\nURL: {r.get('url')}\nDesc: {r.get('description')}\n")
except Exception as e:
    print("Error google-search-scraper:", e)
